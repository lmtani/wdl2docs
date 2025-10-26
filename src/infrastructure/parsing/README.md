# Infrastructure - Parsing Module

Este módulo contém a implementação de infraestrutura para parsing de arquivos WDL, isolando completamente as dependências de bibliotecas externas (miniwdl).

## Arquitetura

A camada de parsing segue os princípios de DDD (Domain-Driven Design):

### 1. **MiniwdlParser** (Facade)
Fachada principal que coordena todas as operações de parsing e retorna objetos de domínio puros.

```python
from pathlib import Path
from src.infrastructure.parsing.miniwdl_parser import MiniwdlParser

# Inicializar o parser
base_path = Path("/home/user/wdl-project")
output_dir = Path("/home/user/docs")
parser = MiniwdlParser(base_path, output_dir)

# Parse um arquivo WDL e obtenha um WDLDocument
wdl_file = base_path / "workflows" / "my_workflow.wdl"
document = parser.parse_document(wdl_file)

# Acessar informações do documento
print(f"Nome: {document.name}")
print(f"Tipo: {document.document_type}")  # "workflow", "tasks", "mixed"
print(f"Tem workflow: {document.has_workflow}")
print(f"Número de tasks: {len(document.tasks)}")

# Acessar workflow
if document.workflow:
    workflow = document.workflow
    print(f"Workflow: {workflow.name}")
    print(f"Inputs: {len(workflow.inputs)}")
    print(f"Outputs: {len(workflow.outputs)}")
    print(f"Calls: {len(workflow.calls)}")
    
    # Docker images usadas
    for docker_image in workflow.docker_images:
        print(f"  - {docker_image.display_image}")
    
    # Grafo Mermaid
    if workflow.has_graph:
        print("Mermaid Graph:")
        print(workflow.mermaid_graph)
```

### 2. **WDLLoader**
Responsável por carregar arquivos WDL usando a biblioteca miniwdl.

```python
from src.infrastructure.parsing.wdl_loader import WDLLoader

loader = WDLLoader()

# Carregar documento WDL
doc, source_code = loader.load_with_source(wdl_file)

# Ou separadamente
doc = loader.load_wdl_file(wdl_file)
source = loader.read_source_code(wdl_file)
version = loader.extract_version(doc)
```

### 3. **PathResolver**
Resolve e normaliza paths de arquivos WDL.

```python
from src.infrastructure.parsing.path_resolver import PathResolver

# Calcular path relativo
relative_path = PathResolver.calculate_relative_path(wdl_file, base_path)

# Normalizar path (lidar com ../ e external/)
normalized = PathResolver.normalize_relative_path(relative_path)

# Resolver import
import_path = PathResolver.resolve_import_path("../external/task.wdl", wdl_file)
```

### 4. **DockerExtractor**
Extrai informações de Docker images de tasks e workflows.

```python
from src.infrastructure.parsing.docker_extractor import DockerExtractor

extractor = DockerExtractor()

# Extrair de um workflow
docker_images = extractor.extract_from_workflow(workflow)

# Extrair de uma task
docker_image = extractor.extract_from_task(task)
```

### 5. **GraphGenerator**
Gera grafos Mermaid a partir de workflows.

```python
from src.infrastructure.parsing.graph_generator import generate_mermaid_graph

# Gerar grafo Mermaid
mermaid_graph = generate_mermaid_graph(workflow, wdl_file, base_path)
```

## Objetos de Domínio

Todos os objetos retornados são objetos de domínio puros (sem dependências de miniwdl):

### WDLDocument
```python
@dataclass
class WDLDocument:
    file_path: Path
    relative_path: Path
    version: str = "1.0"
    workflow: Optional[WDLWorkflow] = None
    tasks: List[WDLTask] = field(default_factory=list)
    imports: List[WDLImport] = field(default_factory=list)
    source_code: Optional[str] = None
```

### WDLWorkflow
```python
@dataclass
class WDLWorkflow:
    name: str
    description: Optional[str] = None
    inputs: List[WDLInput] = field(default_factory=list)
    outputs: List[WDLOutput] = field(default_factory=list)
    calls: List[WDLCall] = field(default_factory=list)
    meta: Dict[str, str] = field(default_factory=dict)
    docker_images: List[WDLDockerImage] = field(default_factory=list)
    mermaid_graph: Optional[str] = None
```

### WDLTask
```python
@dataclass
class WDLTask:
    name: str
    description: Optional[str] = None
    inputs: List[WDLInput] = field(default_factory=list)
    outputs: List[WDLOutput] = field(default_factory=list)
    command: Optional[WDLCommand] = None
    runtime: Dict[str, str] = field(default_factory=dict)
    meta: Dict[str, str] = field(default_factory=dict)
```

## Benefícios da Arquitetura

1. **Isolamento de Dependências**: Toda a dependência do miniwdl está isolada na camada de infraestrutura.

2. **Testabilidade**: É possível testar a lógica de negócio sem depender do miniwdl (usando mocks).

3. **Flexibilidade**: Se precisar trocar o miniwdl por outro parser, apenas a camada de infraestrutura precisa mudar.

4. **Clareza**: A interface do `MiniwdlParser` deixa claro o que entra e o que sai.

5. **Objetos de Domínio Puros**: Os objetos retornados não têm dependências externas e representam conceitos do domínio WDL.

## Exemplo Completo de Uso

```python
from pathlib import Path
from src.infrastructure import MiniwdlParser

def process_wdl_file(wdl_path: Path):
    """Processa um arquivo WDL e imprime informações."""
    
    # Configurar parser
    base_path = wdl_path.parent.parent
    output_dir = Path("docs")
    parser = MiniwdlParser(base_path, output_dir)
    
    # Parse o documento
    doc = parser.parse_document(wdl_path)
    
    # Exibir informações básicas
    print(f"📄 {doc.name}")
    print(f"   Tipo: {doc.document_type}")
    print(f"   Versão WDL: {doc.version}")
    
    # Se tem workflow
    if doc.has_workflow:
        wf = doc.workflow
        print(f"\n🔄 Workflow: {wf.name}")
        
        if wf.description:
            print(f"   {wf.description}")
        
        print(f"\n   📥 Inputs: {len(wf.inputs)}")
        for inp in wf.inputs:
            default = f" = {inp.default_value}" if inp.has_default else ""
            print(f"      - {inp.name}: {inp.type}{default}")
        
        print(f"\n   📤 Outputs: {len(wf.outputs)}")
        for out in wf.outputs:
            print(f"      - {out.name}: {out.type}")
        
        print(f"\n   📞 Calls: {len(wf.calls)}")
        for call in wf.calls:
            call_type_emoji = "🔧" if call.is_task_call else "🔄"
            location = "local" if call.is_local else "external"
            print(f"      {call_type_emoji} {call.display_name} ({location})")
        
        print(f"\n   🐳 Docker Images: {len(wf.docker_images)}")
        for img in wf.docker_images:
            print(f"      - {img.display_image}")
            print(f"        Usado em: {', '.join(img.task_names)}")
    
    # Tasks
    if doc.has_tasks:
        print(f"\n🔧 Tasks: {len(doc.tasks)}")
        for task in doc.tasks:
            print(f"\n   Task: {task.name}")
            if task.description:
                print(f"   {task.description}")
            print(f"   Inputs: {len(task.inputs)}, Outputs: {len(task.outputs)}")
    
    return doc


# Uso
if __name__ == "__main__":
    wdl_file = Path("/path/to/workflow.wdl")
    document = process_wdl_file(wdl_file)
```

## Migração do Código Antigo

Se você está migrando código que usava o `parser.py` antigo:

**Antes:**
```python
import WDL
doc = WDL.load(str(wdl_file))
workflow = doc.workflow
```

**Depois:**
```python
from src.infrastructure import MiniwdlParser

parser = MiniwdlParser(base_path, output_dir)
document = parser.parse_document(wdl_file)
workflow = document.workflow  # Objeto de domínio puro
```

A grande vantagem é que `document.workflow` agora é um objeto de domínio (`WDLWorkflow`), não um objeto miniwdl, o que torna o código mais limpo e testável.
