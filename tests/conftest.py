"""
Pytest configuration and shared fixtures.

This module contains fixtures used across multiple test modules.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_wdl_content():
    """Sample WDL workflow content."""
    return """version 1.0

workflow HelloWorld {
    input {
        String name
        File? optional_file
    }
    
    meta {
        description: "A simple hello world workflow"
    }
    
    call SayHello { input: name = name }
    
    output {
        String greeting = SayHello.message
    }
}

task SayHello {
    input {
        String name
        String docker_image = "ubuntu:20.04"
    }
    
    command <<<
        echo "Hello ~{name}"
    >>>
    
    runtime {
        docker: docker_image
        memory: "2 GB"
        cpu: 2
    }
    
    output {
        String message = read_string(stdout())
    }
}
"""


@pytest.fixture
def sample_task_wdl():
    """Sample WDL task content."""
    return """version 1.0

task ProcessFile {
    input {
        File input_file
        Int threads = 4
        String docker_image = "quay.io/biocontainers/samtools:1.15"
    }
    
    meta {
        description: "Process a file with samtools"
    }
    
    command <<<
        samtools view -@ ~{threads} ~{input_file} > output.bam
    >>>
    
    runtime {
        docker: docker_image
        cpu: threads
        memory: "8 GB"
    }
    
    output {
        File output_bam = "output.bam"
    }
}
"""


@pytest.fixture
def sample_import_wdl():
    """Sample WDL with imports."""
    return """version 1.0

import "tasks/alignment.wdl" as align
import "tasks/variant_calling.wdl" as vc

workflow Pipeline {
    input {
        File fastq
    }
    
    call align.BwaAlign { input: fastq = fastq }
    call vc.CallVariants { input: bam = BwaAlign.output_bam }
    
    output {
        File vcf = CallVariants.variants
    }
}
"""


@pytest.fixture
def sample_scatter_wdl():
    """Sample WDL with scatter block."""
    return """version 1.0

workflow ScatterExample {
    input {
        Array[File] input_files
    }
    
    scatter (file in input_files) {
        call ProcessFile { input: input_file = file }
    }
    
    output {
        Array[File] results = ProcessFile.result
    }
}

task ProcessFile {
    input {
        File input_file
    }
    
    command <<<
        echo "Processing ~{input_file}"
    >>>
    
    output {
        File result = stdout()
    }
}
"""


@pytest.fixture
def create_wdl_file(temp_dir):
    """Factory fixture to create WDL files in temp directory."""

    def _create_file(filename: str, content: str) -> Path:
        file_path = temp_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path

    return _create_file


@pytest.fixture
def create_wdl_structure(temp_dir, sample_wdl_content, sample_task_wdl):
    """Create a complete WDL project structure."""

    def _create_structure():
        # Create internal files
        (temp_dir / "workflows").mkdir(parents=True)
        (temp_dir / "tasks").mkdir(parents=True)
        (temp_dir / "external" / "vendor").mkdir(parents=True)

        # Create workflow file
        workflow_path = temp_dir / "workflows" / "main.wdl"
        workflow_path.write_text(sample_wdl_content)

        # Create task file
        task_path = temp_dir / "tasks" / "process.wdl"
        task_path.write_text(sample_task_wdl)

        # Create external file
        external_path = temp_dir / "external" / "vendor" / "lib.wdl"
        external_path.write_text(sample_task_wdl)

        return {
            "root": temp_dir,
            "workflow": workflow_path,
            "task": task_path,
            "external": external_path,
        }

    return _create_structure
