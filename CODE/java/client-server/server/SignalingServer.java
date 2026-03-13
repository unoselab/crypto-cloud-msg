import java.io.*;
import java.net.*;
import java.util.*;

public class SignalingServer {
    // Stores client username mapped to their network connection and compute score
    static class ClientData {
        PrintWriter out;
        int computeScore;
        public ClientData(PrintWriter out, int computeScore) {
            this.out = out;
            this.computeScore = computeScore;
        }
    }

    // Using a synchronized map is safer when multiple threads are reading/writing
    private static final Map<String, ClientData> clients = Collections.synchronizedMap(new HashMap<>());
    private static int p2pPortAllocator = 6000; 

    public static void main(String[] args) {
        System.out.println("Signaling Server starting on port 5001...");
        try (ServerSocket serverSocket = new ServerSocket(5001)) {
            while (true) {
                Socket clientSocket = serverSocket.accept();
                new ClientHandler(clientSocket).start();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static class ClientHandler extends Thread {
        private Socket socket;
        private BufferedReader in;
        private PrintWriter out;
        private String username;

        public ClientHandler(Socket socket) { this.socket = socket; }

        public void run() {
            try {
                in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
                out = new PrintWriter(socket.getOutputStream(), true);

                // 1. Read the initial registration
                String registration = in.readLine();
                String[] parts = registration.split(" ");
                username = parts[1];
                int computeScore = Integer.parseInt(parts[2]);
                
                clients.put(username, new ClientData(out, computeScore));
                System.out.println(username + " connected with compute score: " + computeScore);
                out.println("[Server] Welcome! You are registered as " + username);

                // 2. Listen for connection requests OR broadcast regular messages
                String message;
                while ((message = in.readLine()) != null) {
                    if (message.startsWith("connection_")) {
                        handleConnectionRequest(message);
                    } else {
                        // NEW: Broadcast the message instead of ignoring it
                        System.out.println("Broadcasting: [" + username + "]: " + message);
                        broadcastMessage("[" + username + "]: " + message);
                    }
                }
            } catch (IOException e) {
                System.out.println(username + " disconnected.");
            } finally {
                if (username != null) {
                    clients.remove(username);
                }
            }
        }

        // NEW: Method to send a message to all connected clients EXCEPT the sender
        private void broadcastMessage(String msg) {
            synchronized (clients) {
                for (Map.Entry<String, ClientData> entry : clients.entrySet()) {
                    if (!entry.getKey().equals(username)) {
                        entry.getValue().out.println(msg);
                    }
                }
            }
        }

        private void handleConnectionRequest(String command) {
            String[] parts = command.split("_");
            if (parts.length != 3) return;
            
            String user1 = parts[1];
            String user2 = parts[2];

            ClientData c1 = clients.get(user1);
            ClientData c2 = clients.get(user2);

            if (c1 == null || c2 == null) {
                out.println("[Server] Error: One or both users are not online.");
                return;
            }

            int p2pPort = p2pPortAllocator++;
            if (c1.computeScore >= c2.computeScore) {
                System.out.println("Assigning " + user1 + " as Host and " + user2 + " as Guest.");
                c1.out.println("CMD_HOST " + p2pPort);
                c2.out.println("CMD_CONNECT 127.0.0.1 " + p2pPort);
            } else {
                System.out.println("Assigning " + user2 + " as Host and " + user1 + " as Guest.");
                c2.out.println("CMD_HOST " + p2pPort);
                c1.out.println("CMD_CONNECT 127.0.0.1 " + p2pPort);
            }
        }
    }
}