
# Tutorial: Como acessar a máquina, configurar o código e instalar as dependências

Este tutorial descreve os passos necessários para acessar sua instância EC2, configurar o código da aplicação, instalar dependências e configurar o Gunicorn para rodar a aplicação Flask de maneira eficiente.

## 1. Acessando a instância EC2 via SSH

1. **Obtenha o IP da sua instância EC2**:
   - No Console de Gerenciamento da AWS, vá para a seção "Instâncias EC2" e encontre o IP público da sua instância.

2. **Configure a chave de acesso (.pem)**:
   - Coloque a chave PEM que foi gerada ao criar sua instância no diretório apropriado no seu sistema local.
   - Altere as permissões da chave para garantir que ela esteja protegida:
     ```bash
     chmod 400 /caminho/para/sua/chave.pem
     ```

3. **Conecte-se à instância via SSH**:
   - Use o comando SSH para conectar-se à sua instância EC2. Supondo que o IP da instância seja `IP_DA_INSTANCIA` e o nome da chave seja `pdfGerar.pem`:
     ```bash
     ssh -i /caminho/para/sua/chave.pem ubuntu@IP_DA_INSTANCIA
     ```
   - Se solicitado, confirme a conexão com "yes".

## 2. Instalar dependências necessárias

Após acessar a instância EC2, siga os passos abaixo para configurar o ambiente.

### 2.1 Atualize os pacotes

Execute o comando abaixo para garantir que o sistema esteja atualizado:
```bash
sudo apt update && sudo apt upgrade -y
2.2 Instale o Python 3 e o pip
Caso o Python 3 não esteja instalado, instale-o com os seguintes comandos:

bash
Mostrar sempre detalhes

Copiar
sudo apt install python3 python3-pip -y
2.3 Instale o Git
Caso o Git não esteja instalado, instale-o com o seguinte comando:

bash
Mostrar sempre detalhes

Copiar
sudo apt install git -y
2.4 Instale o Virtualenv
O virtualenv é uma ferramenta para criar ambientes isolados em Python. Instale-o com o comando:

bash
Mostrar sempre detalhes

Copiar
sudo apt install python3-venv -y
2.5 Criando o ambiente virtual
Crie o ambiente virtual no diretório onde você deseja colocar a aplicação:

bash
Mostrar sempre detalhes

Copiar
python3 -m venv venv
Ative o ambiente virtual:

bash
Mostrar sempre detalhes

Copiar
source venv/bin/activate
2.6 Instalando as dependências do projeto
Suba o código para a instância EC2 (caso ainda não tenha feito) e entre no diretório da aplicação. Dentro desse diretório, instale as dependências listadas no arquivo requirements.txt:

bash
Mostrar sempre detalhes

Copiar
pip install -r requirements.txt
3. Instalando e configurando o Gunicorn
3.1 Instalando o Gunicorn
O Gunicorn é um servidor WSGI para Python, ideal para ambientes de produção. Para instalá-lo, execute:

bash
Mostrar sempre detalhes

Copiar
pip install gunicorn
3.2 Configurando o Gunicorn para rodar a aplicação Flask
Para rodar sua aplicação com o Gunicorn, execute o seguinte comando dentro do diretório da aplicação:

bash
Mostrar sempre detalhes

Copiar
gunicorn --bind 0.0.0.0:5000 app:app
Isso fará com que sua aplicação Flask seja executada na porta 5000 de todas as interfaces de rede da instância EC2.

4. Liberando portas na AWS (Segurança)
Caso você não consiga acessar a aplicação pela web, é necessário liberar a porta 5000 no grupo de segurança da sua instância EC2.

4.1 Acessando o Grupo de Segurança
No Console de Gerenciamento da AWS, vá para "EC2" -> "Security Groups" (Grupos de Segurança).

Encontre o grupo de segurança associado à sua instância e edite as regras de entrada para permitir o tráfego na porta 5000.

Adicione uma regra com as configurações:

Tipo: Custom TCP

Porta: 5000

Origem: 0.0.0.0/0 (para permitir acesso de qualquer IP)

4.2 Verificando se a instância está acessível
Agora, acesse a aplicação via navegador ou usando cURL, por exemplo:

bash
Mostrar sempre detalhes

Copiar
curl http://IP_DA_INSTANCIA:5000
5. Acessando a aplicação via navegador
Após liberar a porta 5000 e iniciar o Gunicorn, você deve ser capaz de acessar sua aplicação através do navegador, utilizando o IP público da sua instância EC2:

cpp
Mostrar sempre detalhes

Copiar
http://IP_DA_INSTANCIA:5000
Se tudo estiver configurado corretamente, a aplicação Flask deverá estar visível.

6. Conclusão
Neste tutorial, você aprendeu como acessar sua instância EC2, configurar o ambiente Python, instalar dependências, configurar o Gunicorn e liberar as portas necessárias para rodar sua aplicação Flask em produção.

Agora, você pode facilmente replicar esse processo para outras instâncias EC2.

Observação: Lembre-se de configurar a segurança adequadamente, permitindo apenas os acessos necessários à sua instância.
