import java.io.*;
import java.net.*;
import java.util.Scanner;

public class HybridClient {
    private static String username;
    private static PrintWriter directOut = null; // Used for P2P messages once connected

    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Usage: java HybridClient <username> <compute_score>");
            return;
        }

        username = args[0];
        String computeScore = args[1];

        try {
            // 1. Connect to Signaling Server
            Socket serverSocket = new Socket("127.0.0.1", 5001);
            PrintWriter serverOut = new PrintWriter(serverSocket.getOutputStream(), true);
            BufferedReader serverIn = new BufferedReader(new InputStreamReader(serverSocket.getInputStream()));

            // Register with the server
            serverOut.println("REGISTER " + username + " " + computeScore);

            // 2. Thread to listen to Server commands
            new Thread(() -> {
                try {
                    String serverMsg;
                    while ((serverMsg = serverIn.readLine()) != null) {
                        if (serverMsg.startsWith("CMD_HOST")) {
                            int port = Integer.parseInt(serverMsg.split(" ")[1]);
                            startP2PHost(port);
                        } else if (serverMsg.startsWith("CMD_CONNECT")) {
                            String[] parts = serverMsg.split(" ");
                            startP2PClient(parts[1], Integer.parseInt(parts[2]));
                        } else {
                            System.out.println("\n" + serverMsg);
                            System.out.print("> ");
                        }
                    }
                } catch (IOException e) {
                    System.out.println("\nDisconnected from Server.");
                }
            }).start();

            // 3. Main thread reads user typing
            Scanner scanner = new Scanner(System.in);
            System.out.println("Type 'connection_<user1>_<user2>' to request a direct link.");
            
            while (true) {
                System.out.print("> ");
                String input = scanner.nextLine();
                
                // If we have a direct connection, send messages there. Otherwise, to the server.
                if (directOut != null && !input.startsWith("connection_")) {
                    directOut.println(input);
                } else {
                    serverOut.println(input);
                }
            }

        } catch (IOException e) {
            System.out.println("Could not connect to Signaling Server.");
        }
    }

    // --- P2P Networking Logic Below ---

    private static void startP2PHost(int port) {
        new Thread(() -> {
            try (ServerSocket serverSocket = new ServerSocket(port)) {
                System.out.println("\n[System] You were assigned as HOST. Opening port " + port + "...");
                Socket peerSocket = serverSocket.accept();
                setupDirectLink(peerSocket);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }).start();
    }

    private static void startP2PClient(String ip, int port) {
        new Thread(() -> {
            try {
                System.out.println("\n[System] You were assigned as GUEST. Connecting to " + ip + ":" + port + "...");
                Thread.sleep(1000); // Brief pause to ensure Host finishes spinning up
                Socket peerSocket = new Socket(ip, port);
                setupDirectLink(peerSocket);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
    }

    private static void setupDirectLink(Socket peerSocket) throws IOException {
        System.out.println("\n[System] DIRECT CONNECTION ESTABLISHED! Your messages are now private.\n> ");
        directOut = new PrintWriter(peerSocket.getOutputStream(), true);
        BufferedReader directIn = new BufferedReader(new InputStreamReader(peerSocket.getInputStream()));

        // Listen for direct messages
        String peerMsg;
        while ((peerMsg = directIn.readLine()) != null) {
            System.out.println("\n[Direct Peer]: " + peerMsg);
            System.out.print("> ");
        }
        System.out.println("\n[System] Direct connection lost.");
        directOut = null; // Revert back to server mode
    }
}