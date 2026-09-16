import com.google.gson.FieldNamingPolicy;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;

import java.util.Arrays;

public class MyApp {
    private static final String[] CAMPOS = {"Name", "EnrollNumber", "Height", "LuckNumbers"};

    // UPPER_CAMEL_CASE: name -> Name, enrollNumber -> EnrollNumber, ...
    private static final Gson GSON = new GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.UPPER_CAMEL_CASE)
            .create();

    public static void main(String[] args) {
        if (args.length > 0) {
            receber(args[0]);
        } else {
            enviar();
        }
    }

    private static void enviar() {
        Person p = new Person();
        p.setName("Ada Lovelace");
        p.setEnrollNumber(100001);
        p.setHeight(1.68f);
        p.setLuckNumbers(Arrays.asList(2, 11, 29));
        System.out.println(GSON.toJson(p));
    }

    private static void receber(String json) {
        JsonObject obj;
        try {
            obj = JsonParser.parseString(json).getAsJsonObject();
        } catch (JsonSyntaxException | IllegalStateException ex) {
            System.out.println("JSON inválido: " + ex.getMessage());
            System.exit(1);
            return;
        }

        for (String campo : CAMPOS) {
            if (!obj.has(campo)) {
                System.out.printf("JSON incompleto: falta a chave \"%s\"\n", campo);
                System.exit(1);
            }
        }

        Person p = GSON.fromJson(obj, Person.class);
        System.out.printf("Name: %s\n", p.getName());
        System.out.printf("EnrollNumber: %d\n", p.getEnrollNumber());
        System.out.printf("Height: %.2f\n", p.getHeight());
        System.out.printf("LuckNumbers: %s\n", p.getLuckNumbers());
    }
}
