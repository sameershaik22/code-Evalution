import java.util.*;

class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        int n = sc.nextInt();
        int target = sc.nextInt();

        int[] arr = new int[n];
        for(int i = 0; i < n; i++) arr[i] = sc.nextInt();

        HashMap<Integer, Integer> mp = new HashMap<>();

        for(int i = 0; i < n; i++) {
            int need = target - arr[i];
            if(mp.containsKey(need)) {
                System.out.println((mp.get(need)+1) + " " + (i+1));
                break;
            }
            mp.put(arr[i], i);
        }
    }
}