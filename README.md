# SaaS Advogado

Um sistema de gestão voltado para escritórios de advocacia, proporcionando uma solução prática e eficiente para a administração de processos, finanças e usuários.

## Tecnologias Utilizadas

- HTML
- Python
- Django (presumido, já que o arquivo `manage.py` está presente)

## Instalação

Para instalar o projeto, siga os passos abaixo:

1. Clone o repositório:
   ```bash
   git clone https://github.com/brunowfull/saasadvogado.git
   ```
2. Navegue até o diretório do projeto:
   ```bash
   cd saasadvogado
   ```
3. Instale as dependências necessárias (se houver um arquivo `requirements.txt`, por exemplo):
   ```bash
   pip install -r requirements.txt
   ```
4. Execute as migrações do banco de dados:
   ```bash
   python manage.py migrate
   ```
5. Crie um usuário de teste:
   ```bash
   python create_test_user.py
   ```
6. Inicie o servidor:
   ```bash
   python manage.py runserver
   ```

## Uso

Após a instalação, você pode acessar o sistema através do navegador em `http://127.0.0.1:8000`.

## Contribuição

Contribuições são bem-vindas! Se você deseja contribuir, siga os passos abaixo:

1. Faça um fork do repositório.
2. Crie uma nova branch:
   ```bash
   git checkout -b minha-contribuicao
   ```
3. Faça suas alterações e commit:
   ```bash
   git commit -m "Adicionando minha contribuição"
   ```
4. Envie para o repositório remoto:
   ```bash
   git push origin minha-contribuicao
   ```
5. Abra um Pull Request.

## Licença

Este projeto não possui licença definida. Sinta-se à vontade para usá-lo como achar melhor.

## Autores

- Bruno W. Full (brunowfull)
