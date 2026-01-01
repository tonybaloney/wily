//! Benchmarks for WilyIndex.analyze_revision method
//!
//! Run with: cargo bench --bench analyze_revision
//! Save baseline: cargo bench --bench analyze_revision -- --save-baseline main
//! Compare: cargo bench --bench analyze_revision -- --baseline main

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use pyo3::Python;
use std::fs;
use tempfile::TempDir;

const SAMPLE_CODE: &str = r#"
def function_{n}(x, y):
    if x > 0:
        for i in range(y):
            if i % 2 == 0:
                print(i)
            else:
                print(i * 2)
    elif x < 0:
        while y > 0:
            y -= 1
    else:
        try:
            result = x / y
        except ZeroDivisionError:
            result = 0
    return x + y

class MyClass_{n}:
    def __init__(self):
        self.value = {n}
    
    def method_a(self, x):
        if x > self.value:
            return x - self.value
        return self.value - x
    
    def method_b(self, y):
        total = 0
        for i in range(y):
            if i % 3 == 0:
                total += i
            elif i % 3 == 1:
                total -= i
            else:
                total *= 2
        return total

def another_function_{n}(a, b, c):
    if a > b:
        if b > c:
            return a
        elif a > c:
            return a
        else:
            return c
    elif b > c:
        return b
    else:
        return c

CONSTANT_{n} = {n} * 100
"#;

fn setup_test_files(count: usize) -> (TempDir, Vec<String>) {
    let temp_dir = TempDir::new().expect("Failed to create temp dir");
    let mut paths = Vec::with_capacity(count);

    for i in 0..count {
        let file_path = temp_dir.path().join(format!("module_{}.py", i));
        let content = SAMPLE_CODE.replace("{n}", &i.to_string());
        fs::write(&file_path, content).expect("Failed to write test file");
        paths.push(file_path.to_string_lossy().to_string());
    }

    (temp_dir, paths)
}

fn bench_analyze_revision(c: &mut Criterion) {
    let mut group = c.benchmark_group("analyze_revision");

    for file_count in [1, 4, 8, 16, 32, 64, 128, 256].iter() {
        let (temp_dir, paths) = setup_test_files(*file_count);
        let base_path = temp_dir.path().to_string_lossy().to_string();
        let operators = vec![
            "raw".to_string(),
            "cyclomatic".to_string(),
            "halstead".to_string(),
            "maintainability".to_string(),
        ];

        group.throughput(Throughput::Elements(*file_count as u64));
        group.bench_with_input(
            BenchmarkId::new("all_operators", file_count),
            &(paths.clone(), base_path.clone(), operators.clone()),
            |b, (paths, base_path, operators)| {
                b.iter(|| {
                    Python::attach(|py| {
                        // Create a new temporary output path for each iteration
                        let output_dir = TempDir::new().expect("Failed to create output dir");
                        let output_path = output_dir
                            .path()
                            .join("metrics.parquet")
                            .to_string_lossy()
                            .to_string();

                        let index = wily_backend::storage::WilyIndex::new_rust(
                            output_path,
                            Some(operators.clone()),
                        );

                        let result = index.analyze_revision_rust(
                            py,
                            black_box(paths.clone()),
                            black_box(base_path.clone()),
                            black_box("abc123def456".to_string()),
                            black_box(1704067200), // 2024-01-01 00:00:00 UTC
                            black_box(Some("Test Author".to_string())),
                            black_box(Some("Test commit message".to_string())),
                        );

                        assert!(result.is_ok(), "Analysis failed: {:?}", result.err());
                    })
                });
            },
        );
    }

    group.finish();
}

fn bench_analyze_revision_by_operator(c: &mut Criterion) {
    let mut group = c.benchmark_group("analyze_revision_by_operator");
    let (temp_dir, paths) = setup_test_files(100);
    let base_path = temp_dir.path().to_string_lossy().to_string();

    // Note: maintainability requires raw metrics for MI calculation
    for (name, ops) in [
        ("raw_only", vec!["raw"]),
        ("cyclomatic_only", vec!["cyclomatic"]),
        ("halstead_only", vec!["halstead"]),
        ("maintainability_with_raw", vec!["raw", "maintainability"]),
        ("raw_cyclomatic", vec!["raw", "cyclomatic"]),
        ("all_operators", vec!["raw", "cyclomatic", "halstead", "maintainability"]),
    ] {
        let operators: Vec<String> = ops.iter().map(|s| s.to_string()).collect();

        group.throughput(Throughput::Elements(100));
        group.bench_with_input(
            BenchmarkId::new("100_files", name),
            &(paths.clone(), base_path.clone(), operators),
            |b, (paths, base_path, operators)| {
                b.iter(|| {
                    Python::attach(|py| {
                        let output_dir = TempDir::new().expect("Failed to create output dir");
                        let output_path = output_dir
                            .path()
                            .join("metrics.parquet")
                            .to_string_lossy()
                            .to_string();

                        let index = wily_backend::storage::WilyIndex::new_rust(
                            output_path,
                            Some(operators.clone()),
                        );

                        let result = index.analyze_revision_rust(
                            py,
                            black_box(paths.clone()),
                            black_box(base_path.clone()),
                            black_box("abc123def456".to_string()),
                            black_box(1704067200),
                            black_box(Some("Test Author".to_string())),
                            black_box(Some("Test commit message".to_string())),
                        );

                        assert!(result.is_ok(), "Analysis failed: {:?}", result.err());
                    })
                });
            },
        );
    }

    group.finish();
}

fn bench_multiple_revisions(c: &mut Criterion) {
    let mut group = c.benchmark_group("multiple_revisions");
    let (temp_dir, paths) = setup_test_files(50);
    let base_path = temp_dir.path().to_string_lossy().to_string();
    let operators = vec![
        "raw".to_string(),
        "cyclomatic".to_string(),
        "halstead".to_string(),
        "maintainability".to_string(),
    ];

    for revision_count in [1, 5, 10, 20].iter() {
        group.throughput(Throughput::Elements(*revision_count as u64));
        group.bench_with_input(
            BenchmarkId::new("50_files", revision_count),
            &(paths.clone(), base_path.clone(), operators.clone(), *revision_count),
            |b, (paths, base_path, operators, rev_count)| {
                b.iter(|| {
                    Python::attach(|py| {
                        let output_dir = TempDir::new().expect("Failed to create output dir");
                        let output_path = output_dir
                            .path()
                            .join("metrics.parquet")
                            .to_string_lossy()
                            .to_string();

                        let index = wily_backend::storage::WilyIndex::new_rust(
                            output_path,
                            Some(operators.clone()),
                        );

                        for i in 0..*rev_count {
                            let result = index.analyze_revision_rust(
                                py,
                                black_box(paths.clone()),
                                black_box(base_path.clone()),
                                black_box(format!("revision_{:04}", i)),
                                black_box(1704067200 + (i as i64 * 86400)), // Each revision 1 day apart
                                black_box(Some("Test Author".to_string())),
                                black_box(Some(format!("Commit message {}", i))),
                            );

                            assert!(result.is_ok(), "Analysis failed: {:?}", result.err());
                        }
                    })
                });
            },
        );
    }

    group.finish();
}

criterion_group!(
    benches,
    bench_analyze_revision,
    bench_analyze_revision_by_operator,
    bench_multiple_revisions
);
criterion_main!(benches);
