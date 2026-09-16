import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

public class Person implements Serializable {
    private String name;
    private int enrollNumber;
    private float height;
    private List<Integer> luckNumbers;

    public Person() {
        name = "";
        enrollNumber = 0;
        height = 0.0f;
        luckNumbers = new ArrayList<>();
    }

    public Person(String name, int enrollNumber, float height, List<Integer> luckNumbers) {
        this.name = name;
        this.enrollNumber = enrollNumber;
        this.height = height;
        this.luckNumbers = new ArrayList<>(luckNumbers);
    }

    public String getName() {
        return this.name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getEnrollNumber() {
        return this.enrollNumber;
    }

    public void setEnrollNumber(int enrollNumber) {
        this.enrollNumber = enrollNumber;
    }

    public float getHeight() {
        return this.height;
    }

    public void setHeight(float height) {
        this.height = height;
    }

    public List<Integer> getLuckNumbers() {
        return this.luckNumbers;
    }

    public void setLuckNumbers(List<Integer> luckNumbers) {
        this.luckNumbers = new ArrayList<>(luckNumbers);
    }
}
