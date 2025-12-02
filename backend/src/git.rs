//! Git archiver implementation using git2-rs.
//!
//! This module provides efficient git history traversal using libgit2,
//! replacing Python's gitpython with native Rust code.

use git2::{
    Commit, Delta, Diff, DiffOptions, ObjectType, Repository, TreeWalkMode, TreeWalkResult,
};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashSet;

/// Information about a single revision/commit
#[derive(Debug, Clone)]
struct RevisionInfo {
    key: String,
    author_name: Option<String>,
    author_email: Option<String>,
    date: i64,
    message: String,
    tracked_files: Vec<String>,
    tracked_dirs: Vec<String>,
    added_files: Vec<String>,
    modified_files: Vec<String>,
    deleted_files: Vec<String>,
}

/// Get all tracked files and directories in a commit's tree
fn get_tracked_files_dirs(commit: &Commit) -> Result<(Vec<String>, Vec<String>), git2::Error> {
    let tree = commit.tree()?;
    let mut files = Vec::new();
    let mut dirs = HashSet::new();

    // Always include root directory
    dirs.insert(String::new());

    tree.walk(TreeWalkMode::PreOrder, |root, entry| {
        let path = if root.is_empty() {
            entry.name().unwrap_or("").to_string()
        } else {
            format!("{}{}", root, entry.name().unwrap_or(""))
        };

        match entry.kind() {
            Some(ObjectType::Blob) => {
                files.push(path.clone());
                // Add parent directories
                let mut parent = std::path::Path::new(&path);
                while let Some(p) = parent.parent() {
                    let dir = p.to_string_lossy().to_string();
                    if !dir.is_empty() {
                        // Use forward slashes for consistency
                        dirs.insert(dir.replace('\\', "/"));
                    }
                    parent = p;
                }
            }
            Some(ObjectType::Tree) => {
                // This is a directory
                let dir_path = if root.is_empty() {
                    entry.name().unwrap_or("").to_string()
                } else {
                    format!("{}{}", root, entry.name().unwrap_or(""))
                };
                if !dir_path.is_empty() {
                    dirs.insert(dir_path.replace('\\', "/"));
                }
            }
            _ => {}
        }
        TreeWalkResult::Ok
    })?;

    let mut dirs_vec: Vec<String> = dirs.into_iter().collect();
    dirs_vec.sort();
    files.sort();

    Ok((files, dirs_vec))
}

/// Result type for file changes: (added, modified, deleted)
type FileChanges = (Vec<String>, Vec<String>, Vec<String>);

/// Get added, modified, and deleted files between two commits
fn whatchanged(
    repo: &Repository,
    new_commit: &Commit,
    old_commit: Option<&Commit>,
) -> Result<FileChanges, git2::Error> {
    let new_tree = new_commit.tree()?;
    let old_tree = old_commit.map(|c| c.tree()).transpose()?;

    let mut diff_opts = DiffOptions::new();
    let diff: Diff =
        repo.diff_tree_to_tree(old_tree.as_ref(), Some(&new_tree), Some(&mut diff_opts))?;

    let mut added = Vec::new();
    let mut modified = Vec::new();
    let mut deleted = Vec::new();

    for delta in diff.deltas() {
        match delta.status() {
            Delta::Added => {
                if let Some(path) = delta.new_file().path() {
                    added.push(path.to_string_lossy().to_string().replace('\\', "/"));
                }
            }
            Delta::Deleted => {
                if let Some(path) = delta.old_file().path() {
                    deleted.push(path.to_string_lossy().to_string().replace('\\', "/"));
                }
            }
            Delta::Modified => {
                if let Some(path) = delta.new_file().path() {
                    modified.push(path.to_string_lossy().to_string().replace('\\', "/"));
                }
            }
            Delta::Renamed => {
                // Renamed = deleted old path + added new path
                if let Some(old_path) = delta.old_file().path() {
                    deleted.push(old_path.to_string_lossy().to_string().replace('\\', "/"));
                }
                if let Some(new_path) = delta.new_file().path() {
                    added.push(new_path.to_string_lossy().to_string().replace('\\', "/"));
                }
            }
            Delta::Copied => {
                // Copied = added new path (old still exists)
                if let Some(path) = delta.new_file().path() {
                    added.push(path.to_string_lossy().to_string().replace('\\', "/"));
                }
            }
            _ => {}
        }
    }

    Ok((added, modified, deleted))
}

/// Get revisions from a git repository.
///
/// This function iterates through the git history and returns revision information
/// as a list of dictionaries that can be converted to Revision instances in Python.
///
/// # Arguments
/// * `repo_path` - Path to the git repository
/// * `max_revisions` - Maximum number of revisions to return
/// * `branch` - Optional branch name (uses HEAD if not provided)
///
/// # Returns
/// A list of dictionaries with revision information, newest first.
#[pyfunction]
#[pyo3(signature = (repo_path, max_revisions, branch=None))]
pub fn get_revisions<'py>(
    py: Python<'py>,
    repo_path: &str,
    max_revisions: usize,
    branch: Option<&str>,
) -> PyResult<Bound<'py, PyList>> {
    let repo = Repository::open(repo_path).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to open repository: {}", e))
    })?;

    // Get the starting commit
    let start_oid = if let Some(branch_name) = branch {
        // Try to resolve as a branch reference first
        if let Ok(reference) = repo.find_branch(branch_name, git2::BranchType::Local) {
            reference.get().target()
        } else {
            // Try as a raw commit SHA
            git2::Oid::from_str(branch_name).ok()
        }
    } else {
        // Use HEAD
        repo.head().ok().and_then(|h| h.target())
    };

    let start_oid = start_oid.ok_or_else(|| {
        pyo3::exceptions::PyValueError::new_err("Could not determine starting commit")
    })?;

    // Set up revwalk
    let mut revwalk = repo.revwalk().map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to create revwalk: {}", e))
    })?;

    revwalk.push(start_oid).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to push starting commit: {}", e))
    })?;

    // Collect commits (oldest first, then we'll reverse for output)
    let mut revisions: Vec<RevisionInfo> = Vec::new();

    // First, collect all commits in reverse order (newest to oldest from revwalk)
    let mut commits: Vec<Commit> = Vec::new();
    for (count, oid_result) in revwalk.enumerate() {
        if count >= max_revisions {
            break;
        }

        let oid = oid_result.map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Error walking revisions: {}", e))
        })?;

        let commit = repo.find_commit(oid).map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Failed to find commit: {}", e))
        })?;

        commits.push(commit);
    }

    // Reverse to get oldest first for processing (matching Python behavior)
    commits.reverse();

    // Now process commits oldest to newest
    for (idx, commit) in commits.iter().enumerate() {
        let (tracked_files, tracked_dirs) = get_tracked_files_dirs(commit).map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Failed to get tracked files: {}", e))
        })?;

        let (added_files, modified_files, deleted_files) = if idx == 0 {
            // First commit: all files are "added"
            (tracked_files.clone(), Vec::new(), Vec::new())
        } else {
            // Get diff from parent commit
            let parent = &commits[idx - 1];
            whatchanged(&repo, commit, Some(parent)).map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(format!("Failed to get changes: {}", e))
            })?
        };

        let author = commit.author();
        let author_name = author.name().map(|s| s.to_string());
        let author_email = author.email().map(|s| s.to_string());

        let rev = RevisionInfo {
            key: commit.id().to_string(),
            author_name,
            author_email,
            date: commit.time().seconds(),
            message: commit.message().unwrap_or("").trim().to_string(),
            tracked_files,
            tracked_dirs,
            added_files,
            modified_files,
            deleted_files,
        };

        revisions.push(rev);
    }

    revisions.reverse();

    let result = PyList::empty(py);

    for rev in revisions {
        let dict = PyDict::new(py);
        dict.set_item("key", rev.key)?;
        dict.set_item("author_name", rev.author_name)?;
        dict.set_item("author_email", rev.author_email)?;
        dict.set_item("date", rev.date)?;
        dict.set_item("message", rev.message)?;

        let tracked_files_list = PyList::new(py, &rev.tracked_files)?;
        dict.set_item("tracked_files", tracked_files_list)?;

        let tracked_dirs_list = PyList::new(py, &rev.tracked_dirs)?;
        dict.set_item("tracked_dirs", tracked_dirs_list)?;

        let added_files_list = PyList::new(py, &rev.added_files)?;
        dict.set_item("added_files", added_files_list)?;

        let modified_files_list = PyList::new(py, &rev.modified_files)?;
        dict.set_item("modified_files", modified_files_list)?;

        let deleted_files_list = PyList::new(py, &rev.deleted_files)?;
        dict.set_item("deleted_files", deleted_files_list)?;

        result.append(dict)?;
    }

    Ok(result)
}

#[pyfunction]
pub fn checkout_revision(repo_path: &str, revision: &str) -> PyResult<()> {
    let repo = Repository::open(repo_path).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to open repository: {}", e))
    })?;

    let obj = repo.revparse_single(revision).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!(
            "Failed to parse revision '{}': {}",
            revision, e
        ))
    })?;

    repo.checkout_tree(&obj, None).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to checkout tree: {}", e))
    })?;

    repo.set_head_detached(obj.id()).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to set HEAD: {}", e))
    })?;

    Ok(())
}

#[pyfunction]
pub fn checkout_branch(repo_path: &str, branch: &str) -> PyResult<()> {
    let repo = Repository::open(repo_path).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to open repository: {}", e))
    })?;

    // Try to find the branch
    let reference = if let Ok(branch_ref) = repo.find_branch(branch, git2::BranchType::Local) {
        branch_ref.into_reference()
    } else {
        // Try as a reference name
        repo.find_reference(&format!("refs/heads/{}", branch))
            .map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(format!(
                    "Failed to find branch '{}': {}",
                    branch, e
                ))
            })?
    };

    let obj = reference.peel_to_commit().map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to peel to commit: {}", e))
    })?;

    repo.checkout_tree(obj.as_object(), None).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to checkout tree: {}", e))
    })?;

    repo.set_head(reference.name().unwrap_or("HEAD"))
        .map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Failed to set HEAD: {}", e))
        })?;

    Ok(())
}

/// Find a specific revision by SHA prefix and return its details.
///
/// This function finds a commit by its SHA prefix (or full SHA) and returns
/// revision information as a dictionary.
///
/// # Arguments
/// * `repo_path` - Path to the git repository
/// * `search` - The SHA prefix or full SHA to search for
///
/// # Returns
/// A dictionary with revision information, or None if not found.
#[pyfunction]
pub fn find_revision<'py>(
    py: Python<'py>,
    repo_path: &str,
    search: &str,
) -> PyResult<Option<Bound<'py, PyDict>>> {
    let repo = Repository::open(repo_path).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to open repository: {}", e))
    })?;

    // Try to resolve the search string as a revision
    let obj = match repo.revparse_single(search) {
        Ok(obj) => obj,
        Err(_) => return Ok(None),
    };

    let commit = match obj.peel_to_commit() {
        Ok(c) => c,
        Err(_) => return Ok(None),
    };

    // Get tracked files and directories
    let (tracked_files, tracked_dirs) = get_tracked_files_dirs(&commit).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Failed to get tracked files: {}", e))
    })?;

    // Get changes from parent
    let parent = commit.parent(0).ok();
    let (added_files, modified_files, deleted_files) = if let Some(ref p) = parent {
        whatchanged(&repo, &commit, Some(p)).map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Failed to get changes: {}", e))
        })?
    } else {
        // First commit: all files are "added"
        (tracked_files.clone(), Vec::new(), Vec::new())
    };

    let author = commit.author();
    let author_name = author.name().map(|s| s.to_string());
    let author_email = author.email().map(|s| s.to_string());

    let dict = PyDict::new(py);
    dict.set_item("key", commit.id().to_string())?;
    dict.set_item("author_name", author_name)?;
    dict.set_item("author_email", author_email)?;
    dict.set_item("date", commit.time().seconds())?;
    dict.set_item("message", commit.message().unwrap_or("").trim().to_string())?;

    let tracked_files_list = PyList::new(py, &tracked_files)?;
    dict.set_item("tracked_files", tracked_files_list)?;

    let tracked_dirs_list = PyList::new(py, &tracked_dirs)?;
    dict.set_item("tracked_dirs", tracked_dirs_list)?;

    let added_files_list = PyList::new(py, &added_files)?;
    dict.set_item("added_files", added_files_list)?;

    let modified_files_list = PyList::new(py, &modified_files)?;
    dict.set_item("modified_files", modified_files_list)?;

    let deleted_files_list = PyList::new(py, &deleted_files)?;
    dict.set_item("deleted_files", deleted_files_list)?;

    Ok(Some(dict))
}

/// Register the git module with the Python module.
pub fn register(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(get_revisions, parent_module)?)?;
    parent_module.add_function(wrap_pyfunction!(find_revision, parent_module)?)?;
    parent_module.add_function(wrap_pyfunction!(checkout_revision, parent_module)?)?;
    parent_module.add_function(wrap_pyfunction!(checkout_branch, parent_module)?)?;
    Ok(())
}
