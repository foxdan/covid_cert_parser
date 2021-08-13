"""Trivial EU Digital Covid Certificate (EUDCC) parser.

Dataspec sheet:
  https://ec.europa.eu/health/sites/default/files/ehealth/docs/covid-certificate_json_specification_en.pdf

Translations of vaccine types, e.g. mRNA, antigen. (key 'vp'):
  https://github.com/ehn-dcc-development/ehn-dcc-schema/blob/a603410d760fefc9073931c8c807759d9714c136/valuesets/vaccine-prophylaxis.json

Translations of vaccine manufacturers (key 'ma'):
  https://github.com/ehn-dcc-development/ehn-dcc-schema/blob/a603410d760fefc9073931c8c807759d9714c136/valuesets/vaccine-mah-manf.json

Translations of vaccine products (key 'mp'):
  https://github.com/ehn-dcc-development/ehn-dcc-schema/blob/a603410d760fefc9073931c8c807759d9714c136/valuesets/vaccine-medicinal-product.json


Notes:
  - base45 was re-implemented here because I didn't like the implementation
    upstream available in PyPI.
  - cbor2 is a required 3p module, I don't event want to know. It took long
    enough to read the RFC.

"""

import argparse
from collections.abc import Iterator
import itertools
import time
from typing import Any
import zlib

import cbor2


TESTDATA = ('HC1:NCFE70X90T9WTWGVLKX49LDA:4NX35 CPX*42BB3XK2F3U7PF9I2F3Z:N3 Q6'
            'JC X8Y50.FK6ZK7:EDOLFVC*70B$D% D3IA4W5646946846.966KCN9E%961A6DL6'
            'FA7D46XJCCWENF6OF63W5NW6C46WJCT3E$B9WJC0FDTA6AIA%G7X+AQB9746QG7$X'
            '8SW6/TC4VCHA7LB7$471S6N-COA7X577:6 47F-CZIC6UCF%6AK4.JCP9EJY8L/5M'
            '/5546.96VF6%JCJQEK69WY8KQEPD09WEQDD+Q6TW6FA7C46TPCBEC8ZKW.C8WE7H8'
            '01AY09ZJC2/D*H8Y3EN3DMPCG/DOUCNB8WY8I3DOUCCECZ CO/EZKEZ964461S6GV'
            'C*JC1A6$473W59%6D4627BPFL .4/FQQRJ/2519D+9D831UT8D4KB82JP63-G$C4/'
            '1B2SMHXDW2V:CSU6NJIO4U0-T6573C+DM-FARF9.3KMF+PVCBD$%K-4PKOE')


MA_DECODE = {'Bharat-Biotech': 'Bharat Biotech',
             'Gamaleya-Research-Institute': 'Gamaleya Research Institute',
             'ORG-100001417': 'Janssen-Cilag International',
             'ORG-100001699': 'AstraZeneca AB',
             'ORG-100006270': 'Curevac AG',
             'ORG-100010771': 'Sinopharm Weiqida Europe Pharmaceutical s.r.o. '
                              '- Prague location',
             'ORG-100013793': 'CanSino Biologics',
             'ORG-100020693': 'China Sinopharm International Corp. - Beijing '
                              'location',
             'ORG-100024420': 'Sinopharm Zhijun (Shenzhen) Pharmaceutical Co. '
                              'Ltd. - Shenzhen location',
             'ORG-100030215': 'Biontech Manufacturing GmbH',
             'ORG-100031184': 'Moderna Biotech Spain S.L.',
             'ORG-100032020': 'Novavax CZ AS',
             'Sinovac-Biotech': 'Sinovac Biotech',
             'Vector-Institute': 'Vector Institute'}


MP_DECODE = {'BBIBP-CorV': 'BBIBP-CorV',
             'CVnCoV': 'CVnCoV',
             'Convidecia': 'Convidecia',
             'CoronaVac': 'CoronaVac',
             'Covaxin': 'Covaxin (also known as BBV152 A, B, C)',
             'EU/1/20/1507': 'COVID-19 Vaccine Moderna',
             'EU/1/20/1525': 'COVID-19 Vaccine Janssen',
             'EU/1/20/1528': 'Comirnaty',
             'EU/1/21/1529': 'Vaxzevria',
             'EpiVacCorona': 'EpiVacCorona',
             'Inactivated-SARS-CoV-2-Vero-Cell': 'Inactivated SARS-CoV-2 (Vero'
                                                 'Cell)',
             'Sputnik-V': 'Sputnik-V'}


def grouper(iterable: Iterator[Any], n_items: int) -> Iterator:
    args = [iter(iterable)] * n_items
    return itertools.zip_longest(*args, fillvalue=None)


B45_CHRSET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'
def b45decode(b45encoded: str) -> Iterator[int]:
    chr_codes = (B45_CHRSET.index(rchr) for rchr in b45encoded)
    for _c, _d, _e in grouper(chr_codes, 3):
        _n = _c + _d*45 + (_e or 0)*45*45
        if _e is not None:
            yield _n >> 8  # Byte A
        yield 0xff & _n    # Byte B


def parse_payload(raw_qr_data: str) -> dict:
    deflate_data = bytes(b45decode(raw_qr_data))
    cbor_web_token = cbor2.loads(zlib.decompress(deflate_data))
    # We only use the payload, additional fields are listed to ease extension.
    protected, unprotected, payload, signature = cbor_web_token.value
    return cbor2.loads(payload)


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('infile', type=argparse.FileType('r'), nargs='?')
    group.add_argument('--test', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.test:
        _input = TESTDATA
    else:
        _input = args.infile.read().strip()
    payload = parse_payload(_input[4:])
    issue_time = time.gmtime(payload[6])
    expire_time = time.gmtime(payload[4])
    payload = payload[-260][1]
    name = payload['nam']
    vax_data = payload['v'][0]
    print("# Identity Info")
    print(f"SURNAME(S):\t{name['fn']}")
    print(f"FORENAME(S):\t{name['gn']}")
    print(f"ID SURNAME(S):\t{name['fnt']}")
    print(f"ID FORENAME(S):\t{name['gnt']}")
    print(f"DOB:\t\t{payload['dob']}")
    print("\n# Vaccine Info")
    print(f"Doses (rcvd/rqrd):\t{vax_data['dn']:g}/{vax_data['sd']:g}")
    print(f"Latest Dose Date:\t{vax_data['dt']}")
    print(f"Manufacturer:\t\t{MA_DECODE[vax_data['ma']]}")
    print(f"Product:\t\t{MP_DECODE[vax_data['mp']]}")
    print("\n#Cert Info:")
    issue_str = time.strftime("%a, %d %b %Y %H:%M:%S +0000", issue_time)
    print(f"Issue Date:\t{issue_str}")
    expire_str = time.strftime("%a, %d %b %Y %H:%M:%S +0000", expire_time)
    print(f"Expire Date:\t{expire_str}")


if __name__ == '__main__':
    main()
