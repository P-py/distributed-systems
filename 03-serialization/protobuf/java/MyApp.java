import com.google.protobuf.InvalidProtocolBufferException;

import java.util.Base64;

/**
 * Recupera o Person serializado pelo lado Python: decodifica o base64 do
 * argumento (ou o stream de amostra da constante) e imprime os campos.
 */
public class MyApp {
    // Dados de amostra: o base64 não é criptografia, quem tiver a string lê
    // todos os campos em claro.
    private static final String BASE64 = "CgtBbGFuIFR1cmluZxCy8hkdXI/iPyIDBxcv";

    public static void main(String[] args) {
        if (args.length > 1) {
            System.out.println("uso: java MyApp [base64]");
            System.exit(2);
        }
        String encoded = args.length == 1 ? args[0] : BASE64;

        try {
            Person p = Person.parseFrom(Base64.getDecoder().decode(encoded));

            System.out.printf("Name: %s%n", p.getName());
            System.out.printf("EnrollNumber: %d%n", p.getEnrollNumber());
            System.out.printf("Height: %.2f%n", p.getHeight());
            System.out.printf("LuckNumbers: %s%n", p.getLuckNumbersList());

            if (encode(p).equals(encoded)) {
                System.out.println("OK: objeto recuperado integralmente (re-serialização idêntica)");
            } else {
                System.out.println("ATENÇÃO: a re-serialização não bate com a entrada");
                System.exit(1);
            }
        } catch (IllegalArgumentException ex) {
            System.out.println("Base64 inválido: " + ex.getMessage());
            System.exit(1);
        } catch (InvalidProtocolBufferException ex) {
            System.out.println("Falha ao desserializar: " + ex.getMessage());
            System.exit(1);
        }
    }

    static String encode(Person p) {
        return Base64.getEncoder().encodeToString(p.toByteArray());
    }
}
