import importlib
import sys

from designdojo import codegen
from designdojo.problems import get_problem


def test_python_contract_is_importable(tmp_path, monkeypatch):
    c = get_problem("parking-lot").contract
    codegen.write_files(tmp_path, codegen.contract_files(c, "python"))
    codegen.write_files(tmp_path, codegen.stub_files(c, "python"))
    monkeypatch.syspath_prepend(str(tmp_path))
    for mod in ("contract", "solution"):
        sys.modules.pop(mod, None)
    contract = importlib.import_module("contract")
    solution = importlib.import_module("solution")
    assert contract.Ticket("T1", "KA01", 1, contract.SpotSize.SMALL, "S1", 0).floor == 1
    assert issubclass(contract.LotFull, Exception)
    assert callable(solution.create)
    for mod in ("contract", "solution"):
        sys.modules.pop(mod, None)


def test_java_contract_shapes():
    files = codegen.contract_files(get_problem("parking-lot").contract, "java")
    api = files["contract/ParkingLotApi.java"]
    assert "Ticket park(String plate, VehicleType vehicleType);" in api
    assert "@throws LotFull" in api
    assert "public record Ticket(String id, String plate, int floor, SpotSize spotSize, String spotId, long entryTime) {}" \
        in files["contract/Ticket.java"]
    assert "hourlyRateCents = Map.copyOf(hourlyRateCents);" in files["contract/LotConfig.java"]
    assert "extends RuntimeException" in files["contract/InvalidTicket.java"]
    stub = codegen.stub_files(get_problem("parking-lot").contract, "java")["solution/Solution.java"]
    assert "public static ParkingLotApi create(LotConfig config, Clock clock)" in stub
