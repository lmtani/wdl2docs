# Configuração do GitHub Pages

## Passos para habilitar o GitHub Pages

1. **Configure a variável do repositório alvo**
   - Vá para: `https://github.com/lmtani/wdl2docs/settings/variables/actions`
   - Ou navegue: **Settings** → **Secrets and variables** → **Actions** → aba **Variables**
   - Clique em **"New repository variable"**
   - **Name**: `TARGET_REPOSITORY`
   - **Value**: `lmtani/sscita-assembly-pipelines` (ou outro repositório no formato `owner/repo`)
   - Clique em **"Add variable"**
   
   > ⚠️ **Nota**: Se você não criar esta variável, o workflow usará o valor padrão `lmtani/sscita-assembly-pipelines`

2. **Acesse as configurações do repositório**
   - Vá para: `https://github.com/lmtani/wdl2docs/settings`

3. **Configure o GitHub Pages**
   - No menu lateral esquerdo, clique em **"Pages"**
   - Em **"Source"**, selecione **"GitHub Actions"**
   - Salve as configurações

4. **Execute o workflow**
   - Vá para a aba **"Actions"** do repositório
   - Selecione o workflow **"Generate and Deploy Documentation"**
   - Clique em **"Run workflow"** → **"Run workflow"**
   
   Ou simplesmente faça um push na branch `main` para disparar automaticamente

4. **Acesse a documentação**
   - Após o workflow concluir (leva alguns minutos), a documentação estará disponível em:
   - `https://lmtani.github.io/wdl2docs/`

## Alterando o repositório alvo

Para documentar um repositório diferente:

1. Vá para: **Settings** → **Secrets and variables** → **Actions** → aba **Variables**
2. Clique no lápis ao lado de `TARGET_REPOSITORY`
3. Altere o **Value** para outro repositório (formato: `owner/repo`)
   - Exemplo: `lmtani/outro-pipeline`
   - Exemplo: `usuario/meu-wdl-repo`
4. Clique em **"Update variable"**
5. Execute o workflow novamente em **Actions** → **Run workflow**

## Como funciona o workflow

O workflow `docs.yml` realiza as seguintes etapas:

1. **Build Job:**
   - Faz checkout do repositório wdl2docs
   - Instala Python 3.13
   - Instala o wdl2docs
   - Clona o repositório definido na variável `TARGET_REPOSITORY`
   - Gera a documentação HTML
   - Faz upload dos arquivos como artefato

2. **Deploy Job:**
   - Publica os arquivos gerados no GitHub Pages
   - Disponibiliza a URL da documentação

## Triggers do workflow

O workflow é executado automaticamente quando:
- Há um push na branch `main`
- É executado manualmente via interface do GitHub Actions

Em ambos os casos, usa o repositório definido na variável `TARGET_REPOSITORY`.

## Configuração do repositório alvo

O workflow usa a variável `TARGET_REPOSITORY` configurada em:
- **Settings** → **Secrets and variables** → **Actions** → **Variables**

**Comportamento:**
- Se a variável `TARGET_REPOSITORY` estiver configurada: usa o valor definido
- Se a variável não existir: usa o padrão `lmtani/sscita-assembly-pipelines`

**Formato**: `owner/repo` (repositório público do GitHub)

**Exemplos:**
- `lmtani/sscita-assembly-pipelines` (padrão)
- `lmtani/outro-pipeline`
- `seu-usuario/seu-wdl-repo`

## Permissões necessárias

O workflow já está configurado com as permissões necessárias:
- `contents: read` - Para ler o código do repositório
- `pages: write` - Para escrever no GitHub Pages
- `id-token: write` - Para autenticação OIDC

## Verificação

Para verificar se tudo está funcionando:

1. Vá para **Actions** e confirme que o workflow executou com sucesso
2. Vá para **Settings** → **Pages** e verifique se há um link verde com a URL do site
3. Clique na URL ou acesse `https://lmtani.github.io/wdl2docs/`

## Solução de problemas

Se o workflow falhar:

1. **Erro de permissões**: Verifique se as permissões de Actions estão habilitadas em Settings → Actions → General
2. **Python 3.13 não disponível**: O GitHub Actions pode não ter Python 3.13. Ajuste para `3.12` ou `3.11` se necessário
3. **Erro na geração**: Verifique os logs do workflow para detalhes específicos

## Atualizações automáticas

A cada push na branch `main`, o workflow irá:
1. Regenerar a documentação do repositório definido em `TARGET_REPOSITORY`
2. Atualizar automaticamente o GitHub Pages

Para gerar documentação de outro repositório:
1. Altere a variável `TARGET_REPOSITORY` em **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. Execute o workflow manualmente em **Actions** → **Run workflow**

Ou simplesmente execute o workflow manualmente sem alterar a variável para regenerar a documentação do repositório atual.
