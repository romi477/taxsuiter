from itertools import combinations
from collections import namedtuple
from decimal import Decimal
from pprint import pprint
import json

from quickbooks.objects.salesreceipt import SalesReceipt


with open('./template.txt', 'r') as f:
    txt = f.read()
    txt_json = json.loads(txt)
    record = SalesReceipt.from_json(txt_json)


class TaxSuiter:

    def __init__(self, record):
        self._record = record
        self._lines = self._parse_product_line()
        self._taxes = self._parse_tax_detail()

    @property
    def lines(self):
        return [x for x in self._lines if x.taxable]

    @property
    def taxes(self):
        return [x for x in self._taxes if x.percent_based]

    def line_combinations(self):
        list_combinations = list()

        for n in range(0, len(self.lines) + 1):
            list_combinations.extend(
                list(combinations(self.lines, n))
            )

        return list_combinations

    def find_combinations(self):
        combinations = self.line_combinations()
        return [self._find_match(tax, combinations) for tax in self.taxes]

    def _find_match(self, tax, combinations):
        amount = tax.net_amount

        for combi in combinations:
            x_amount = sum(map(lambda x: x.amount, combi))

            if str(x_amount) == amount:
                return tax, combi

        return tuple()

    def _parse_product_line(self):
        Line = namedtuple('Line', 'id amount tax_class taxable')

        def serialize(line):
            return Line(
                line.LineNum,
                Decimal(str(line.Amount)),
                line.SalesItemLineDetail['TaxClassificationRef']['value'],
                line.SalesItemLineDetail['TaxCodeRef']['value'] == 'TAX',
            )

        return [serialize(x) for x in self._record.Line if hasattr(x, 'SalesItemLineDetail')]

    def _parse_tax_detail(self):
        Tax = namedtuple('Tax', 'id amount percent_based net_amount')

        def serialize(tax):
            return Tax(
                tax.TaxLineDetail.TaxRateRef.value,
                str(tax.Amount),
                tax.TaxLineDetail.PercentBased,
                str(tax.TaxLineDetail.NetAmountTaxable),
            )

        return [serialize(x) for x in self._record.TxnTaxDetail.TaxLine]


rec = TaxSuiter(record)
res = rec.find_combinations()

pprint(res)
