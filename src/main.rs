package br.ufu.facom.gbc074.kvs;

import org.eclipse.paho.client.mqttv3.MqttException;
import java.io.IOException;

public class Main {
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Uso: Main <porta>");
            System.exit(1);
        }

        int port = Integer.parseInt(args[0]);
        
        try {
            KVSServer server = new KVSServer(port);
            server.start();
            server.blockUntilShutdown();
        } catch (MqttException | IOException | InterruptedException e) {
            System.err.println("Erro ao iniciar o servidor: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}