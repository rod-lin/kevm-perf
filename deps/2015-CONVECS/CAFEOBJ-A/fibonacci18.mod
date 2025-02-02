-- CAFEOBJ-A
mod! Fibonacci18 {
  [ Xnat ]
  op d0 : -> Xnat { constr }
  op s : Xnat -> Xnat { constr }
  op plus : Xnat Xnat -> Xnat
  op fibb : Xnat -> Xnat
  eq plus (d0, N:Xnat) = N .
  eq plus (s (N:Xnat), M:Xnat) = s (plus (N, M)) .
  eq fibb (d0) = d0 .
  eq fibb (s (d0)) = s (d0) .
  eq fibb (s (s (N:Xnat))) = plus (fibb (s (N)), fibb (N)) .
}
select Fibonacci18 .
red fibb (s (s (s (s (s (s (s (s (s (s (s (s (s (s (s (s (s (s (d0))))))))))))))))))) .
