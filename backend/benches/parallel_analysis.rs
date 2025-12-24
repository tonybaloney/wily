//! Benchmarks for parallel file analysis
//!
//! Run with: cargo bench
//! Save baseline: cargo bench -- --save-baseline main
//! Compare: cargo bench -- --baseline main

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

fn bench_parallel_analysis(c: &mut Criterion) {
    let mut group = c.benchmark_group("analyze_files_parallel");

    for file_count in [1, 4, 8, 16, 32, 64, 256, 512].iter() {
        let (_temp_dir, paths) = setup_test_files(*file_count);
        let operators = vec![
            "raw".to_string(),
            "cyclomatic".to_string(),
            "halstead".to_string(),
            "maintainability".to_string(),
        ];

        group.throughput(Throughput::Elements(*file_count as u64));
        group.bench_with_input(
            BenchmarkId::new("all_operators", file_count),
            &(paths, operators),
            |b, (paths, operators)| {
                b.iter(|| {
                    Python::attach(|py| {
                        let _ = wily_backend::parallel::analyze_files_parallel(
                            py,
                            black_box(paths.clone()),
                            black_box(operators.clone()),
                        )
                        .expect("Analysis failed");
                    })
                });
            },
        );
    }

    group.finish();
}

fn bench_individual_operators(c: &mut Criterion) {
    let mut group = c.benchmark_group("individual_operators");
    let (_temp_dir, paths) = setup_test_files(100);

    for (name, ops) in [
        ("raw", vec!["raw"]),
        ("cyclomatic", vec!["cyclomatic"]),
        ("halstead", vec!["halstead"]),
        ("maintainability", vec!["maintainability"]),
    ] {
        let operators: Vec<String> = ops.iter().map(|s| s.to_string()).collect();

        group.throughput(Throughput::Elements(100));
        group.bench_with_input(BenchmarkId::new("100_files", name), &operators, |b, ops| {
            b.iter(|| {
                Python::attach(|py| {
                    let _ = wily_backend::parallel::analyze_files_parallel(
                        py,
                        black_box(paths.clone()),
                        black_box(ops.clone()),
                    )
                    .expect("Analysis failed");
                })
            });
        });
    }

    group.finish();
}

criterion_group!(benches, bench_parallel_analysis, bench_individual_operators);
criterion_main!(benches);
