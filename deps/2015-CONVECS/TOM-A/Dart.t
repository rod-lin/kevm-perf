// TOM-A
import dart.term.*;
import dart.term.types.*;
public class Dart {
  %gom{
    module Term
    abstract syntax
    Set =
      | add(rec_x1_1:Set, rec_x2_1:Set)
      | allops()
      | doubles()
      | empty()
      | finish()
      | flat(rec_x1_2:Set, rec_x2_2:Set)
      | mult(rec_x1_3:Set, rec_x2_3:Set)
      | singles()
      | singleton(rec_x1_4:Xnat)
      | triples()
      | union(rec_x1_5:Set, rec_x2_5:Set)
      | u(rec_x1_6:Set, rec_x2_6:Set)
    Xnat =
      | d0()
      | fifteen()
      | fifty()
      | five()
      | plus(rec_x1_1:Xnat, rec_x2_1:Xnat)
      | s(rec_x1_2:Xnat)
      | ten()
      | times(rec_x1_3:Xnat, rec_x2_3:Xnat)
      | twentyfive()
    module Term:rules() {
      plus (d0(), N) -> N
      plus (s (N), M) -> s (plus (N, M))
      times (d0(), N) -> d0()
      times (s (N), M) -> plus (M, times (N, M))
      u (empty(), S0) -> S0
      u (S0, empty()) -> S0
      u (S0, S1) -> S0 if S0 ==S1
      u (S0, S1) -> flat (S0, flat (S1, empty())) if S0 != S1
      flat (empty(), S0) -> S0
      flat (singleton (I), S0) -> union (singleton (I), S0)
      flat (union (S1, S2), S0) -> flat (S1, flat (S2, S0))
      add (empty(), S0) -> S0
      add (S0, empty()) -> S0
      add (singleton (I), singleton (J)) -> singleton (plus (I, J))
      add (singleton (I), union (singleton (J), S0)) -> add (singleton (plus (I, J)), S0)
      add (union (singleton (I), S1), S2) -> u (add (singleton (I), S2), add (S1, S2))
      mult (empty(), S0) -> S0
      mult (S0, empty()) -> S0
      mult (singleton (I), singleton (J)) -> singleton (times (I, J))
      mult (union (singleton (I), S1), S2) -> u (mult (singleton (I), S2), mult (S1, S2))
      five() -> s (s (s (s (s (d0())))))
      ten() -> s (s (s (s (s (five())))))
      fifteen() -> s (s (s (s (s (ten())))))
      twentyfive() -> s (s (s (s (s (s (s (s (s (s (fifteen()))))))))))
      fifty() -> plus (twentyfive(), twentyfive())
      singles() -> add (singleton (s (d0())), add (singleton (s (s (d0()))), add (singleton (s (s (s (d0())))),add (singleton (s (s (s (s (d0()))))), add (singleton (five()),add (singleton (s (five())), add (singleton (s (s (five()))),add (singleton (s (s (s (five())))), add (singleton (s (s (s (s (five()))))), add (singleton (ten()), add (singleton (s (ten())), add (singleton (s (s (ten()))),add (singleton (s (s (s (ten())))), add (singleton (s (s (s (s (ten()))))), add (singleton (fifteen()),add (singleton (s (fifteen())), add (singleton (s (s (fifteen()))), add (singleton (s (s (s (fifteen())))), add (singleton (s (s (s (s (fifteen()))))), singleton (plus (five(), fifteen())))))))))))))))))))))
      doubles() -> mult (singles(), singleton (s (s (d0()))))
      triples() -> mult (singles(), singleton (s (s (s (d0())))))
      allops() -> u (u (u (u (u (singles(), doubles()), triples()), singleton (twentyfive())), singleton (fifty())), singleton (d0()))
      finish() -> add (u (doubles(), singleton (fifty())), add (allops(), allops()))
    }
  }
  public static void main (String[] args) {
    System.out.println (`finish());
  }
}
