import requests
import json
from datetime import datetime
from typing import List
import graphyte


class AirParameter:
    _name: str = ''
    _norma: float = 0.0
    _pdk: float = 0.0
    _value: float = 0.0
    _last_update: datetime = 0
    _chemicalFormula: str = ''

    def __init__(self, name: str, norma: float, pdk: float, value: float, datetime_str: str, chemical_formula: str):
        self._name = name
        self._norma = norma
        self._pdk = pdk
        self._value = value
        self._chemicalFormula = chemical_formula

        self._last_update = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')

    @property
    def name(self) -> str:
        return self._name

    @property
    def norma(self) -> float:
        return self._norma

    @property
    def pdk(self) -> float:
        return self._pdk

    @property
    def value(self) -> float:
        return self._value

    @property
    def last_update_seconds(self) -> int:
        a_timedelta = self._last_update - datetime(1900, 1, 1)
        return int(a_timedelta.total_seconds())

    @property
    def chemicalFormula(self) -> str:
        return self._chemicalFormula

    def __str__(self):
        return "%s (%s): %.4f/%.2f (%.2f ПДК). Updated at %s" % (
            self.name,
            self.chemicalFormula,
            self.value,
            self.norma,
            self.pdk,
            self._last_update
        )


class AirState:
    _parameters: List[AirParameter] = list()
    _station: str = ''

    def __init__(self, station: str):
        self._station = station

        r = requests.post(
            'https://mosecom.mos.ru/wp-content/themes/moseco/map/station-popup.php',
            data={
                'locale': 'ru_RU',
                'station_name': station,
                'mapType': 'air'
            }
        )
        if r.status_code == 200:
            parameters = json.loads(r.text)['parameters']
            for p in parameters:
                try:
                    self._parameters.append(
                        AirParameter(
                            p['name'],
                            p['norma'],
                            p['pdk'],
                            p['modifyav'],
                            p['dateTime'],
                            p['chemicalFormula']
                        )
                    )
                except KeyError:
                    pass

    def __iter__(self):
        return iter(self._parameters)

    def __str__(self):
        response: str = ''
        for p in self._parameters:
            response += "%s\n" % p
        return response

    def send_to_graphite(self, host: str, prefix: str = 'air.state'):
        graphyte.init(host, prefix="%s.%s" % (prefix, self._station))
        for p in self.parameters:
            ts = p.last_update_seconds
            graphyte.send(
                metric=p.chemicalFormula + ".pdk",
                value=p.norma,
                timestamp=ts
            )

            graphyte.send(
                metric=p.chemicalFormula + ".value",
                value=p.value,
                timestamp=ts
            )
