"""
Genera las cuotas de un periodo y aplica recargos a las vencidas.
Pensado para correr desde un cron el dia 1 de cada mes (es idempotente).

  python generar_cuotas.py             (mes actual)
  python generar_cuotas.py 2026-10
"""
import sys
from datetime import date

import cuotas

periodo = sys.argv[1] if len(sys.argv) > 1 else cuotas.periodo_de(date.today())
if not cuotas.periodo_valido(periodo):
    raise SystemExit("Periodo invalido, usar AAAA-MM")

r = cuotas.generar_cuotas(periodo)
r["recargos"] = cuotas.aplicar_recargos()
print(r)
