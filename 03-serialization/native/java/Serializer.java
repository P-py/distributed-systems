import java.io.ByteArrayOutputStream;
import java.io.ObjectOutputStream;
import java.io.IOException;
import java.util.Arrays;
import java.util.Base64;

public class Serializer {
    public static void main(String[] args) {
        Person p = new Person();
        p.setName("Alan Turing");
        p.setEnrollNumber(424242);
        p.setHeight(1.77f);
        p.setLuckNumbers(Arrays.asList(7, 23, 47));
        try {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ObjectOutputStream oos = new ObjectOutputStream(baos);
            oos.writeObject(p);
            oos.flush();
            oos.close();
            String encoded = Base64.getEncoder().encodeToString(baos.toByteArray());
            baos.close();
            System.out.printf("Base64: %s\n", encoded);
        } catch (IOException ex) {
            System.out.println("IOException while serializaing!");
        }
    }
}
