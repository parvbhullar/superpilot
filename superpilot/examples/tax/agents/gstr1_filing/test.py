import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

import asyncio


# Flow executor -> Context
#
# Context -> Search & Summarise [WebSearch, KnowledgeBase, News] - parrallel] -> Context
# Context -> Analysis[FinancialAnalysis] -> Context
# Context -> Write[TextStream, PDF, Word] -> Context
# Context -> Respond[Twitter, Email, Stream]] -> Context
# Context -> Finalise[PDF, Word] -> Context


query = """
    Supplier GSTIN	Invoice Status	Transaction Number	Supply Type	Invoice No.	Invoice Date	Invoice Type	Note Number	Note Date	HSN/SAC	Item Description	Quantity	UQC (unit of measure)	Invoice Value	Note Value	Taxable Value	GST Rate	IGST Amount	CGST Amount	SGST/UTGST Amount	CESS Amount	Revenue Account	Customer GSTIN	Customer Name	Place of Supply	Export Type	Shipping Bill Number	Shipping Bill Date	Port Number	GSTR1 Return Period	3B Auto-fill Period	Location	isamended	Document Number	Document Date	Reverse Charge	Original Invoice Number	Original Invoice Date	Original Month	Amortised cost
27GSPMH0591G1ZK	Add	23210417	Normal	800/50	29-08-2021	Tax Invoice			0208		25.56	KGS	3068		45600.56	18	8208.1008	0	0	25.65	21.8500.111.150430.0000.000000.0000.000000.000000.00000000	33GSPTN9511G3Z3	IPM INDIA WHOLESALE TRADING PVT LTD	9					08-2021	082021	Delhi		GHTY/1200-005	15-02-2022					
27GSPMH0591G1ZK	Add	23210417	Normal	800/51	29-08-2021	Tax Invoice			0208		25.56	KGS	3068		85900.56	18	0	7731.0504	7731.0504	50.56	21.8500.111.150430.0000.000000.0000.000000.000000.00000000	33GSPTN9511G3Z3	IPM INDIA WHOLESALE TRADING PVT LTD	27					08-2021	082021	Delhi		GHTY/1200-005	15-02-2022					
27GSPMH0591G1ZK	Add	23210418	Normal	800/52	29-08-2021	Tax Invoice			9102		35.65	NOS	28910		256890.67	12	30826.8804	0	0	50.56	21.8500.111.150430.0000.000000.0000.000000.000000.00000000		IPM INDIA WHOLESALE TRADING PVT LTD	9					08-2021	082021	Delhi		GHTY/1200-005	15-02-2022					
27GSPMH0591G1ZK	Add	23210419	Normal	800/53	29-08-2021	Tax Invoice			0208		27.56	KGS	10620		236800.65	5	11840.0325	0	0	0	21.8500.111.150430.0000.000000.0000.000000.000000.00000000		IPM INDIA WHOLESALE TRADING PVT LTD	9					08-2021	082021	Delhi		GHTY/1200-005	15-02-2022					
27GSPMH0591G1ZK	Add	23210419	Normal	800/54	29-08-2021	Tax Invoice			0208		27.56	KGS	10620		237800.65	5	0	5945.01625	5945.01625	78.89	21.8500.111.150430.0000.000000.0000.000000.000000.00000000		IPM INDIA WHOLESALE TRADING PVT LTD	27					08-2021	082021	Delhi		GHTY/1200-005	15-02-2022					
    """


def run_executor():
    from services.gstgptservice.agents.gstr1_filing.executor import Gstr1FillingExecutor
    # from s
    executor = Gstr1FillingExecutor()
    asyncio.run(executor.run(query))


if __name__ == "__main__":
    # asyncio.run(test_pilot())
    run_executor()
