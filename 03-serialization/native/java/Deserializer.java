import java.io.ByteArrayInputStream;
import java.io.ObjectInputStream;
import java.io.IOException;
import java.util.Base64;

public class Deserializer {
 public static void main(String[] args) {
  try {
     byte[] decoded = Base64.getDecoder().decode("rO0ABXNyAAZQZXJzb27XA7FpGjZTSgIABEkADGVucm9sbE51bWJlckYABmhlaWdodEwAC2x1Y2tOdW1iZXJzdAAQTGphdmEvdXRpbC9MaXN0O0wABG5hbWV0ABJMamF2YS9sYW5nL1N0cmluZzt4cAAGeTI/4o9cc3IAE2phdmEudXRpbC5BcnJheUxpc3R4gdIdmcdhnQMAAUkABHNpemV4cAAAAAN3BAAAAANzcgARamF2YS5sYW5nLkludGVnZXIS4qCk94GHOAIAAUkABXZhbHVleHIAEGphdmEubGFuZy5OdW1iZXKGrJUdC5TgiwIAAHhwAAAAB3NxAH4ABgAAABdzcQB+AAYAAAAveHQAC0FsYW4gVHVyaW5n"); // Stream de amostra
     ByteArrayInputStream bais = new ByteArrayInputStream(decoded);
     ObjectInputStream ois = new ObjectInputStream(bais);
     Person p = (Person) ois.readObject();
     ois.close();
     bais.close();
     System.out.printf("Name: %s\n", p.getName());
     System.out.printf("EnrollNumber: %d\n", p.getEnrollNumber());
     System.out.printf("Height: %.2f\n", p.getHeight());
     System.out.printf("LuckNumbers: %s\n", p.getLuckNumbers());    
  } catch (ClassNotFoundException ex) {
     System.out.println("ClassNotFoundException while serializaing!");
  } catch (IOException ex) {
     System.out.println("IOException while serializaing!");
  }
 }
}