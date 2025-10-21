import java.util.Scanner;

public class Main {
    // Method to encrypt the message
    public static String encrypt(String plaintext, int shift) {
        StringBuilder result = new StringBuilder();

        for (int i = 0; i < plaintext.length(); i++) {
            char ch = plaintext.charAt(i);

            if (ch >= 'a' && ch <= 'z') {
                ch = (char) ((ch - 'a' + shift) % 26 + 'a');
            } else if (ch >= 'A' && ch <= 'Z') {
                ch = (char) ((ch - 'A' + shift) % 26 + 'A');
            }

            result.append(ch);
        }

        return result.toString();
    }

    // Method to decrypt the message
    public static String decrypt(String ciphertext, int shift) {
        StringBuilder result = new StringBuilder();

        for (int i = 0; i < ciphertext.length(); i++) {
            char ch = ciphertext.charAt(i);

            if (ch >= 'a' && ch <= 'z') {
                ch = (char) (ch - shift);
                if (ch < 'a') {
                    ch = (char) (ch + 26);
                }
            } else if (ch >= 'A' && ch <= 'Z') {
                ch = (char) (ch - shift);
                if (ch < 'A') {
                    ch = (char) (ch + 26);
                }
            }

            result.append(ch);
        }

        return result.toString();
    }

    // Main method (entry point)
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        System.out.println("Caesar Cipher Program");
        System.out.println("1. Encrypt a message");
        System.out.println("2. Decrypt a message");
        System.out.print("Choose an option (1 or 2): ");
        int choice = sc.nextInt();
        sc.nextLine(); // consume the leftover newline

        if (choice == 1) {
            System.out.print("Enter the plaintext message: ");
            String plaintext = sc.nextLine();
            System.out.print("Enter the shift value: ");
            int shift = sc.nextInt();
            String encrypted = encrypt(plaintext, shift);
            System.out.println("Encrypted message: " + encrypted);
        } else if (choice == 2) {
            System.out.print("Enter the ciphertext message: ");
            String ciphertext = sc.nextLine();
            System.out.print("Enter the shift value: ");
            int shift = sc.nextInt();
            String decrypted = decrypt(ciphertext, shift);
            System.out.println("Decrypted message: " + decrypted);
        } else {
            System.out.println("Invalid choice. Please run the program again.");
        }

        sc.close();
    }
}
