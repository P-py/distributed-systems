import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.util.Base64;

/**
 * Recupera o Person a partir do base64 gerado pelo Serializer: usa o argumento
 * da linha de comando quando existe, senão o stream de amostra da constante.
 */
public class Deserializer {
    private static final String BASE64 =
            "rO0ABXNyAAZQZXJzb27XA7FpGjZTSgIABEkADGVucm9sbE51bWJlckYABmhlaWdodEwAC2x1Y2tOdW1iZXJzdAAQTGphdmEvdXRpbC9MaXN0O0wABG5hbWV0ABJMamF2YS9sYW5nL1N0cmluZzt4cAAGeTI/4o9cc3IAE2phdmEudXRpbC5BcnJheUxpc3R4gdIdmcdhnQMAAUkABHNpemV4cAAAAAN3BAAAAANzcgARamF2YS5sYW5nLkludGVnZXIS4qCk94GHOAIAAUkABXZhbHVleHIAEGphdmEubGFuZy5OdW1iZXKGrJUdC5TgiwIAAHhwAAAAB3NxAH4ABgAAABdzcQB+AAYAAAAveHQAC0FsYW4gVHVyaW5n";

    public static void main(String[] args) {
        if (args.length > 1) {
            System.out.println("uso: java Deserializer [base64]");
            System.exit(2);
        }
        String encoded = args.length == 1 ? args[0] : BASE64;

        byte[] decoded;
        try {
            decoded = Base64.getDecoder().decode(encoded);
        } catch (IllegalArgumentException ex) {
            System.out.println("Base64 inválido: " + ex.getMessage());
            System.exit(1);
            return;
        }

        try {
            Person p;
            try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(decoded))) {
                p = (Person) ois.readObject();
            }

            System.out.printf("Name: %s%n", p.getName());
            System.out.printf("EnrollNumber: %d%n", p.getEnrollNumber());
            System.out.printf("Height: %.2f%n", p.getHeight());
            System.out.printf("LuckNumbers: %s%n", p.getLuckNumbers());

            // Person não implementa equals(), e acrescentá-lo mudaria o
            // serialVersionUID padrão da classe: a conferência é feita
            // re-serializando o objeto e comparando com o stream de entrada.
            if (Serializer.encode(p).equals(encoded)) {
                System.out.println("OK: objeto recuperado integralmente (re-serialização idêntica)");
            } else {
                System.out.println("ATENÇÃO: a re-serialização não bate com a entrada");
                System.exit(1);
            }
        } catch (ClassNotFoundException | IOException ex) {
            // A exceção real nomeia o problema (header inválido, classe
            // incompatível, classe ausente do classpath); um catch genérico
            // com mensagem fixa esconderia justamente isso.
            System.out.println("Falha ao desserializar: " + ex);
            System.exit(1);
        }
    }
}
