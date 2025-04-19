#!/bin/bash

# Verifica e instala dependências do sistema
echo "Instalando dependências do sistema..."
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    build-essential

# Instala Rust e Cargo
echo "Instalando Rust e Cargo..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Configura ambiente Python
echo "Configurando ambiente Python..."
python3 -m venv venv
source venv/bin/activate

# Instala dependências Python
echo "Instalando dependências Python..."
pip install --upgrade pip
pip install grpcio grpcio-tools paho-mqtt

# Compila o protobuf
echo "Compilando protobuf..."
python -m grpc_tools.protoc -I./proto --python_out=./src --grpc_python_out=./src ./proto/kvs.proto

# Corrige imports gerados pelo protobuf
echo "Corrigindo imports..."
sed -i 's/import kvs_pb2/from src import kvs_pb2/g' ./src/kvs_pb2_grpc.py

# Baixa e compila o cliente Rust se necessário
if [ -d "kvs-client" ]; then
    echo "Compilando cliente Rust..."
    cd kvs-client
    cargo build
    cd ..
fi

# Cria scripts auxiliares
echo "Criando scripts auxiliares..."

# server.sh
cat > server.sh << 'EOL'
#!/bin/bash
source venv/bin/activate
python src/server.py $1
EOL

# teste.sh
cat > teste.sh << 'EOL'
#!/bin/bash
source venv/bin/activate
./teste1-insere.sh
sleep 2
./teste2-consulta.sh
sleep 2
./teste3-remove.sh
sleep 2
./teste4-snapshot.sh
EOL

# client.sh
cat > client.sh << 'EOL'
#!/bin/bash
source venv/bin/activate
python src/client.py "$@"
EOL

# Dá permissões de execução
chmod +x server.sh teste.sh client.sh

echo "Configuração concluída com sucesso!"

# Inicia os servidores em terminais separados (opcional - descomente se quiser execução automática)
# x-terminal-emulator -e ./server.sh 9000
# x-terminal-emulator -e ./server.sh 9001
# x-terminal-emulator -e ./server.sh 9002
# sleep 5
# x-terminal-emulator -e ./teste.sh

echo "Para executar o sistema:"
echo "1. Abra 3 terminais e execute em cada um:"
echo "   ./server.sh 9000"
echo "   ./server.sh 9001" 
echo "   ./server.sh 9002"
echo "2. Em outro terminal execute:"
echo "   ./teste.sh"