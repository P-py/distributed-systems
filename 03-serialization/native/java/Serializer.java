import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.util.Arrays;
import java.util.Base64;

/**
 * Serializa um Person com o ObjectOutputStream da JVM e imprime o stream em
 * base64. O base64 não é criptografia: quem tiver a string lê todos os campos.
 * Por isso os valores abaixo são dados de amostra.
 */
public class Serializer {
    public static void main(String[] args) {
        Person p = new Person();
        p.setName("Alan Turing");
        p.setEnrollNumber(424242);
        p.setHeight(1.77f);
        p.setLuckNumbers(Arrays.asList(7, 23, 47));

        try {
            System.out.printf("Base64: %s%n", encode(p));
        } catch (IOException ex) {
            System.out.println("Falha ao serializar: " + ex);
            System.exit(1);
        }
    }

    /** Usado também pelo Deserializer, para validar a volta re-serializando. */
    static String encode(Person p) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ObjectOutputStream oos = new ObjectOutputStream(baos)) {
            oos.writeObject(p);
        }
        return Base64.getEncoder().encodeToString(baos.toByteArray());
    }
}
