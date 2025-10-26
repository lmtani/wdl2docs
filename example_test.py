"""Example to demonstrate workflow call tracking in documentation."""
from pathlib import Path
from src.domain.value_objects import WDLDocument, WDLWorkflow, WDLCall, WDLInput, WDLType
from src.infrastructure.rendering.generator import DocumentationGenerator
from src.infrastructure.templating.asset_copier import AssetCopier
import tempfile
import shutil

# Create temporary directories
temp_dir = Path(tempfile.mkdtemp())
output_dir = temp_dir / "docs"
output_dir.mkdir()

print(f"Output directory: {output_dir}")

# Create a subworkflow that will be called by multiple workflows
bam_processing = WDLDocument(
    file_path=temp_dir / "subworkflows/bam_processing.wdl",
    relative_path=Path("subworkflows/bam_processing.wdl"),
    version="1.0",
    workflow=WDLWorkflow(
        name="BamProcessing",
        description="Process BAM files with quality control and metrics",
        inputs=[
            WDLInput(
                name="input_bam",
                type=WDLType(name="File", optional=False),
                description="Input BAM file to process",
            )
        ],
        outputs=[],
        calls=[],
        meta={},
        docker_images=[],
    ),
    tasks=[],
    imports=[],
)

# Create main workflow 1 that calls the subworkflow
illumina_workflow = WDLDocument(
    file_path=temp_dir / "workflows/illumina/ngs/exome/AlignIlluminaReads.wdl",
    relative_path=Path("workflows/illumina/ngs/exome/AlignIlluminaReads.wdl"),
    version="1.0",
    workflow=WDLWorkflow(
        name="AlignIlluminaReads",
        description="Align Illumina reads and process BAM files",
        inputs=[],
        outputs=[],
        calls=[
            WDLCall(
                name="bam_proc",
                task_or_workflow="BamProcessing",
                call_type="workflow",
            )
        ],
        meta={},
        docker_images=[],
    ),
    tasks=[],
    imports=[],
)

# Create main workflow 2 that also calls the subworkflow
genome_workflow = WDLDocument(
    file_path=temp_dir / "workflows/illumina/ngs/genome/WholeGenomeAnalysis.wdl",
    relative_path=Path("workflows/illumina/ngs/genome/WholeGenomeAnalysis.wdl"),
    version="1.0",
    workflow=WDLWorkflow(
        name="WholeGenomeAnalysis",
        description="Complete whole genome analysis pipeline",
        inputs=[],
        outputs=[],
        calls=[
            WDLCall(
                name="process_bams",
                task_or_workflow="BamProcessing",
                call_type="workflow",
            )
        ],
        meta={},
        docker_images=[],
    ),
    tasks=[],
    imports=[],
)

# Create a standalone workflow (not called by anyone)
standalone_workflow = WDLDocument(
    file_path=temp_dir / "workflows/StandaloneWorkflow.wdl",
    relative_path=Path("workflows/StandaloneWorkflow.wdl"),
    version="1.0",
    workflow=WDLWorkflow(
        name="StandaloneWorkflow",
        description="A workflow that is not called by other workflows",
        inputs=[],
        outputs=[],
        calls=[],
        meta={},
        docker_images=[],
    ),
    tasks=[],
    imports=[],
)

# Generate documentation
all_docs = [bam_processing, illumina_workflow, genome_workflow, standalone_workflow]
templates_dir = Path(__file__).parent / "src" / "infrastructure" / "rendering" / "templates"
asset_copier = AssetCopier(templates_dir)
generator = DocumentationGenerator(output_dir, temp_dir, asset_copier)

print("Generating documentation...")
success = generator.execute(all_docs, [])

if success:
    print(f"✓ Documentation generated successfully!")
    print(f"\nCheck the following files:")
    print(f"  - {output_dir / 'subworkflows/bam_processing.html'}")
    print(f"    (should show: 'This workflow is called as a subworkflow by 2 other workflows')")
    print(f"  - {output_dir / 'workflows/StandaloneWorkflow.html'}")
    print(f"    (should NOT show subworkflow usage section)")
    
    # Read and show excerpt from the subworkflow page
    subworkflow_page = output_dir / "subworkflows/bam_processing.html"
    if subworkflow_page.exists():
        content = subworkflow_page.read_text()
        if "Subworkflow Usage" in content:
            print("\n✓ Subworkflow usage section found in BamProcessing.html")
            # Find the section
            start = content.find("Subworkflow Usage")
            if start > 0:
                excerpt = content[max(0, start-100):min(len(content), start+500)]
                print("\nExcerpt:")
                print(excerpt[:300] + "...")
        else:
            print("\n✗ Subworkflow usage section NOT found in BamProcessing.html")
    
    # Check standalone workflow
    standalone_page = output_dir / "workflows/StandaloneWorkflow.html"
    if standalone_page.exists():
        content = standalone_page.read_text()
        if "Subworkflow Usage" not in content:
            print("\n✓ Standalone workflow correctly has NO subworkflow usage section")
        else:
            print("\n✗ Standalone workflow incorrectly shows subworkflow usage section")
else:
    print("✗ Documentation generation failed!")

# Cleanup
# shutil.rmtree(temp_dir)
print(f"\nTemporary files kept in: {temp_dir}")
