use clap::{Parser, ValueEnum};
use kvs::kvs_client::KvsClient;
use kvs::{ChaveValor, ChaveVersao, Versao};
use tonic::Request;

pub mod kvs {
    tonic::include_proto!("kvs");
}

/// Portal Cadastro Client
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// Server IP address
    #[arg(short, long, default_value_t = String::from("127.0.0.1"))]
    address: String,
    /// Server port
    #[arg(required = true, short, long, default_value_t = 9000)]
    port: u16,
    /// Operation
    #[arg(value_enum, short, long, default_value_t = Operation::Consulta)]
    op: Operation,
    /// Key(s) (operation dependant)
    ///
    /// # Example
    ///
    /// To insert a new key/value, run:
    /// `cargo run-- -p 9000 -o insere -k key1234 -v value1234`
    #[arg(short, long)]
    key: Vec<String>,
    /// Value(s) (operation dependant)
    #[arg(short, long)]
    val: Vec<String>,
    /// Version(s) (operation dependant)
    #[arg(short = 'e', long)]
    ver: Vec<i32>,
}

/// Allowed operations
#[derive(ValueEnum, Clone, Debug, PartialEq)]
enum Operation {
    Insere,
    Consulta,
    Remove,
    InsereV,
    ConsultaV,
    RemoveV,
    Snapshot,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    let mut client = KvsClient::connect(format!("http://{}:{}", args.address, args.port)).await?;

    let key = args.key;
    let val = args.val;
    let ver = args.ver;

    let reply: String = match args.op {
        Operation::Consulta => {
            assert!(key.len() == 1, "Informe uma chave!");
            let cv = ChaveVersao {
                chave: key.first().unwrap().to_string(),
                versao: ver.first().copied(),
            };
            format!(
                "{:?}",
                client
                    .consulta(Request::new(cv))
                    .await
                    .unwrap()
                    .into_inner()
            )
        }
        Operation::Insere => {
            assert!(key.len() == 1, "Informe uma chave!");
            assert!(val.len() == 1, "Informe um valor!");
            let kv = ChaveValor {
                chave: key.first().unwrap().to_string(),
                valor: val.first().unwrap().to_string(),
            };
            format!(
                "{:?}",
                client.insere(Request::new(kv)).await.unwrap().into_inner()
            )
        }
        Operation::Remove => {
            assert!(key.len() == 1, "Informe uma chave!");
            let cv = ChaveVersao {
                chave: key.first().unwrap().to_string(),
                versao: ver.first().copied(),
            };
            format!(
                "{:?}",
                client.remove(Request::new(cv)).await.unwrap().into_inner()
            )
        }
        Operation::ConsultaV => {
            assert!(!key.is_empty(), "Informe ao menos uma chave!");
            assert!(
                ver.is_empty() || ver.len() == key.len(),
                "Informe uma versão para cada chave ou não informe nenhuma!"
            );
            let x: Vec<ChaveVersao> = if ver.is_empty() {
                key.iter()
                    .map(|k| ChaveVersao {
                        chave: k.to_string(),
                        versao: Some(0),
                    })
                    .collect()
            } else {
                key.iter()
                    .zip(ver.iter())
                    .map(|(k, e)| ChaveVersao {
                        chave: k.to_string(),
                        versao: Some(*e),
                    })
                    .collect()
            };
            let request = Request::new(tokio_stream::iter(x));
            let mut stream = client.consulta_varias(request).await?.into_inner();
            let mut s = String::new();
            while let Some(tupla) = stream.message().await? {
                s += format!("{:?}\n", tupla).as_str();
            }
            s
        }
        Operation::InsereV => {
            assert!(
                !key.is_empty() && !val.is_empty(),
                "Informe ao menos uma chave e um valor!"
            );
            assert!(
                val.len() == key.len(),
                "Quantidade de chaves e de valores deve ser a mesma!"
            );
            let x: Vec<ChaveValor> = key
                .iter()
                .zip(val.iter())
                .map(|(k, v)| ChaveValor {
                    chave: k.to_string(),
                    valor: v.to_string(),
                })
                .collect();
            let request = Request::new(tokio_stream::iter(x));
            let mut stream = client.insere_varias(request).await?.into_inner();
            let mut s = String::new();
            while let Some(e) = stream.message().await? {
                s += format!("{:?}\n", e).as_str();
            }
            s
        }
        Operation::RemoveV => {
            assert!(!key.is_empty(), "Informe ao menos uma chave!");
            assert!(
                ver.is_empty() || ver.len() == key.len(),
                "Informe uma versão para cada chave ou não informe nenhuma!"
            );
            let x: Vec<ChaveVersao> = if ver.is_empty() {
                key.iter()
                    .map(|k| ChaveVersao {
                        chave: k.to_string(),
                        versao: Some(0),
                    })
                    .collect()
            } else {
                key.iter()
                    .zip(ver.iter())
                    .map(|(k, e)| ChaveVersao {
                        chave: k.to_string(),
                        versao: Some(*e),
                    })
                    .collect()
            };
            let request = Request::new(tokio_stream::iter(x));
            let mut stream = client.remove_varias(request).await?.into_inner();
            let mut s = String::new();
            while let Some(e) = stream.message().await? {
                s += format!("{:?}\n", e).as_str();
            }
            s
        }
        Operation::Snapshot => {
            assert!(ver.len() == 1, "Informe a versão!");
            let v = ver.first().copied();
            let mut stream = client
                .snapshot(Request::new(Versao { versao: v.unwrap() }))
                .await?
                .into_inner();
            let mut s = String::new();
            while let Some(tupla) = stream.message().await? {
                s += format!("{:?}\n", tupla).as_str();
            }
            s
        }
    };
    println!("Reply = {}\n", reply);
    Ok(())
}