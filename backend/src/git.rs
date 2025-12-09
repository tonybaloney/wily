//! Git archiver implementation using git2-rs.
//!
//! This module provides efficient git history traversal using libgit2,
//! replacing Python's gitpython with native Rust code.

use git2::{
    Commit, Delta, Diff, DiffOptions, ObjectType, Repository, TreeWalkMode, TreeWalkResult,
};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::files::is_python_filename;

/// Information about a single revision/commit
#[derive(Debug, Clone)]
struct RevisionInfo {
    key: String,
    author_name: Option<String>,
    author_email: Option<String>,
    date: i64,
    message: String,
    added_files: Vec<String>,
    modified_files: Vec<String>,
    deleted_files: Vec<String>,
}

impl RevisionInfo {
    fn from_commit(
        commit: &Commit,
        added_files: Vec<String>,
        modified_files: Vec<String>,
        deleted_files: Vec<String>,
    ) -> Self {
        let author = commit.author();
        let author_name = author.name().map(|s| s.to_string());
        let author_email = author.email().map(|s| s.to_string());

        RevisionInfo {
            key: commit.id().to_string(),
            author_name,
            author_email,
            date: commit.time().seconds(),
            message: commit.message().unwrap_or("").trim().to_string(),
            added_files,
            modified_files,
            deleted_files,
        }
    }

    fn to_py_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("key", &self.key)?;
        dict.set_item("author_name", &self.author_name)?;
        dict.set_item("author_email", &self.author_email)?;
        dict.set_item("date", self.date)?;
        dict.set_item("message", &self.message)?;

        let added_files_list = PyList::new(py, &self.added_files)?;
        dict.set_item("added_files", added_files_list)?;

        let modified_files_list = PyList::new(py, &self.modified_files)?;
        dict.set_item("modified_files", modified_files_list)?;

        let deleted_files_list = PyList::new(py, &self.deleted_files)?;
        dict.set_item("deleted_files", deleted_files_list)?;

        Ok(dict)
    }
}

/// Get all tracked files and directories in a commit's tree
fn get_tracked_files(commit: &Commit, include_ipynb: bool) -> Result<Vec<String>, git2::Error> {
    let tree = commit.tree()?;
    let mut files = Vec::new();

    tree.walk(TreeWalkMode::PreOrder, |root, entry| {
        let path = if root.is_empty() {
            entry.name().unwrap_or("").to_string()
        } else {
            format!("{}{}", root, entry.name().unwrap_or(""))
        };

        if let Some(ObjectType::Blob) = entry.kind() {
            if is_python_filename(&path, include_ipynb) {
                files.push(path);
            }
        }
        TreeWalkResult::Ok
    })?;

    files.sort(); // TODO: Does this need to be sorted?

    Ok(files)
}

/// Result type for file changes: (added, modified, deleted)
type FileChanges = (Vec<String>, Vec<String>, Vec<String>);

/// Get added, modified, and deleted Python files between two commits
fn whatchanged(
    repo: &Repository,
    new_commit: &Commit,
    old_commit: Option<&Commit>,
    include_ipynb: bool,
) -> Result<FileChanges, git2::Error> {
    let new_tree = new_commit.tree()?;
    let old_tree = old_commit.map(|c| c.tree()).transpose()?;

    let mut diff_opts = DiffOptions::new();
    let diff: Diff =
        repo.diff_tree_to_tree(old_tree.as_ref(), Some(&new_tree), Some(&mut diff_opts))?;

    let mut added = Vec::new();
    let mut modified = Vec::new();
    let mut deleted = Vec::new();

    // TODO: Try and remove this \\ / normalization logic.

    for delta in diff.deltas() {
        match delta.status() {
            Delta::Added => {
                if let Some(path) = delta.new_file().path() {
                    if is_python_filename(&path.to_string_lossy(), include_ipynb) {
                        added.push(path.to_string_lossy().to_string().replace('\\', "/"));
                    }
                }
            }
            Delta::Deleted => {
                if let Some(path) = delta.old_file().path() {
                    if is_python_filename(&path.to_string_lossy(), include_ipynb) {
                        deleted.push(path.to_string_lossy().to_string().replace('\\', "/"));
                    }
                }
            }
            Delta::Modified => {
                if let Some(path) = delta.new_file().path() {
                    if is_python_filename(&path.to_string_lossy(), include_ipynb) {
                        modified.push(path.to_string_lossy().to_string().replace('\\', "/"));
                    }
                }
            }
            Delta::Renamed => {
                // Renamed = deleted old path + added new path
                if let Some(old_path) = delta.old_file().path() {
                    if is_python_filename(&old_path.to_string_lossy(), include_ipynb) {
                        deleted.push(old_path.to_string_lossy().to_string().replace('\\', "/"));
                    }
                }
                if let Some(new_path) = delta.new_file().path() {
                    if is_python_filename(&new_path.to_string_lossy(), include_ipynb) {
                        added.push(new_path.to_string_lossy().to_string().replace('\\', "/"));
                    }
                }
            }
            Delta::Copied => {
                // Copied = added new path (old still exists)
                if let Some(path) = delta.new_file().path() {
                    if is_python_filename(&path.to_string_lossy(), include_ipynb) {
                        added.push(path.to_string_lossy().to_string().replace('\\', "/"));
                    }
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
/// An iterator of revision info
#[pyfunction]
#[pyo3(signature = (repo_path, max_revisions, branch=None, include_ipynb=true))]
pub fn get_revisions(
    _py: Python<'_>,
    repo_path: &str,
    max_revisions: usize,
    branch: Option<&str>,
    include_ipynb: bool,
) -> PyResult<RevisionIterator> {
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

    // First, collect all commit OIDs in reverse order (newest to oldest from revwalk)
    let mut commit_oids: Vec<git2::Oid> = Vec::new();
    for (count, oid_result) in revwalk.enumerate() {
        if count >= max_revisions {
            break;
        }

        let oid = oid_result.map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Error walking revisions: {}", e))
        })?;

        commit_oids.push(oid);
    }

    // Reverse to get oldest first from the iterator
    commit_oids.reverse();

    let iterator = RevisionIterator {
        commit_oids,
        index: 0,
        repo,
        include_ipynb,
    };
    Ok(iterator)
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
#[pyo3(signature = (repo_path, search, include_ipynb = true))]
pub fn find_revision<'py>(
    py: Python<'py>,
    repo_path: &str,
    search: &str,
    include_ipynb: bool,
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

    // Get changes from parent
    let parent = commit.parent(0).ok();
    let (added_files, modified_files, deleted_files) = if let Some(ref p) = parent {
        whatchanged(&repo, &commit, Some(p), include_ipynb).map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Failed to get changes: {}", e))
        })?
    } else {
        // Get tracked files
        let tracked_files = get_tracked_files(&commit, include_ipynb).map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Failed to get tracked files: {}", e))
        })?;
        // First commit: all files are "added"
        (tracked_files.clone(), Vec::new(), Vec::new())
    };

    let rev = RevisionInfo::from_commit(&commit, added_files, modified_files, deleted_files);
    let dict = rev.to_py_dict(py)?;

    Ok(Some(dict))
}

#[pyclass(unsendable)]
pub struct RevisionIterator {
    commit_oids: Vec<git2::Oid>,
    index: usize,
    repo: Repository,
    include_ipynb: bool,
}

#[pymethods]
impl RevisionIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __len__(&self) -> PyResult<usize> {
        Ok(self.commit_oids.len())
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<Py<PyDict>>> {
        if self.index < self.commit_oids.len() {
            let oid = self.commit_oids[self.index];
            let commit = self.repo.find_commit(oid).map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(format!("Failed to find commit: {}", e))
            })?;

            // Now process commits oldest to newest
            let (added_files, modified_files, deleted_files) = if self.index == 0 {
                // First commit: all files are "added"
                let tracked_files =
                    get_tracked_files(&commit, self.include_ipynb).map_err(|e| {
                        pyo3::exceptions::PyValueError::new_err(format!(
                            "Failed to get tracked files: {}",
                            e
                        ))
                    })?;
                (tracked_files.clone(), Vec::new(), Vec::new())
            } else {
                // Get diff from parent commit
                let parent_oid = self.commit_oids[self.index - 1];
                let parent = self.repo.find_commit(parent_oid).map_err(|e| {
                    pyo3::exceptions::PyValueError::new_err(format!(
                        "Failed to find parent commit: {}",
                        e
                    ))
                })?;
                whatchanged(&self.repo, &commit, Some(&parent), self.include_ipynb).map_err(
                    |e| {
                        pyo3::exceptions::PyValueError::new_err(format!(
                            "Failed to get changes: {}",
                            e
                        ))
                    },
                )?
            };

            let rev =
                RevisionInfo::from_commit(&commit, added_files, modified_files, deleted_files);
            self.index += 1;
            Ok(Some(rev.to_py_dict(py)?.into()))
        } else {
            Ok(None)
        }
    }
}

/// Register the git module with the Python module.
pub fn register(parent_module: &Bound<'_, PyModule>) -> PyResult<()> {
    parent_module.add_function(wrap_pyfunction!(get_revisions, parent_module)?)?;
    parent_module.add_function(wrap_pyfunction!(find_revision, parent_module)?)?;
    parent_module.add_function(wrap_pyfunction!(checkout_revision, parent_module)?)?;
    parent_module.add_function(wrap_pyfunction!(checkout_branch, parent_module)?)?;
    parent_module.add_class::<RevisionIterator>()?;
    Ok(())
}
