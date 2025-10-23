import os
import requests
import json
import pandas as pd
from datetime import datetime
from requests import Response

def format_bulk_stocks_eod(ticker: str, df: pd.DataFrame) -> bytes:
    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quant-agents_stocks-eod_{today}"
    lines = []

    for _, row in df.iterrows():

        date_reference = row.get('timestamp')
        open_ = row.get('open')
        close = row.get('close')
        high = row.get('high')
        low = row.get('low')
        volume = row.get('volume')

        if open_ is None or close is None:
            continue
        id_str = f"{ticker}_{str(date_reference)}"

        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "date_reference": date_reference,
            "val_open": float(open_),
            "val_close": float(close) if close is not None else None,
            "val_high": float(high) if high is not None else None,
            "val_low": float(low) if low is not None else None,
            "val_volume": int(volume) if volume is not None else None,
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")

def ingest_stocks_eod(ticker: str) -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
    alpha_vantage_api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    alpha_vantage_time_series_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={alpha_vantage_api_key}&datatype=csv"

    ticker_daily_time_series = pd.read_csv(alpha_vantage_time_series_url)

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_stocks_eod(ticker, ticker_daily_time_series)
    )


def format_bulk_stocks_insider_trades(ticker: str, df: pd.DataFrame) -> bytes:
    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quant-agents_stocks-insider-trades_{today}"
    lines = []

    for _, row in df.iterrows():

        date_reference = row.get('transaction_date').strftime('%Y-%m-%d')
        executive = row.get('executive')
        executive_title = row.get('executive_title')
        acquisition_or_disposal = row.get('acquisition_or_disposal')
        shares= row.get('shares')
        share_price = row.get('share_price')

        id_str = f"{ticker}_{date_reference}"

        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "date_reference": date_reference,
            "text_executive_name": executive,
            "text_executive_title": executive_title,
            "key_acquisition_disposal": acquisition_or_disposal,
            "val_share_quantity": float(shares),
            "val_share_price": float(share_price)
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")

def ingest_stocks_insider_trades(ticker: str, cutoff_days=100) -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
    alpha_vantage_api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    alpha_vantage_insider_trades_url = f"https://www.alphavantage.co/query?function=INSIDER_TRANSACTIONS&symbol={ticker}&apikey={alpha_vantage_api_key}"

    ticker_insider_trades_data = requests.get(alpha_vantage_insider_trades_url).json()
    df = pd.json_normalize(ticker_insider_trades_data['data'])
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors='coerce')
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=cutoff_days)
    ticker_recent_insider_trades = df[df["transaction_date"] >= cutoff].reset_index(drop=True)

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_stocks_insider_trades(ticker, ticker_recent_insider_trades)
    )

def format_bulk_stocks_metadata(ticker: str, df: pd.DataFrame) -> bytes:
    import json
    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quant-agents_stocks-metadata_{today}"
    lines = []

    for _, row in df.iterrows():
        # canonical values, accept multiple key variants
        symbol = row.get('Symbol') or ticker
        asset_type = row.get('AssetType')
        name = row.get('Name')
        description = row.get('Description')
        cik = row.get('CIK')
        exchange = row.get('Exchange')
        currency = row.get('Currency')
        country = row.get('Country')
        sector = row.get('Sector')
        industry = row.get('Industry')
        address = row.get('Address')
        official_site = row.get('OfficialSite')
        fiscal_year_end = row.get('FiscalYearEnd')

        latest_quarter = row.get('LatestQuarter')
        dividend_date = row.get('DividendDate')
        ex_dividend_date = row.get('ExDividendDate')

        # numeric conversions
        market_capitalization = int(row.get('MarketCapitalization'))
        ebitda = int(row.get('EBITDA'))
        pe_ratio = float(row.get('PERatio'))
        peg_ratio = float(row.get('PEGRatio'))
        book_value = float(row.get('BookValue'))
        dividend_per_share = float(row.get('DividendPerShare'))
        dividend_yield = float(row.get('DividendYield'))
        eps = float(row.get('EPS'))
        revenue_per_share_ttm = float(row.get('RevenuePerShareTTM'))
        profit_margin = float(row.get('ProfitMargin'))
        operating_margin_ttm = float(row.get('OperatingMarginTTM'))
        return_on_assets_ttm = float(row.get('ReturnOnAssetsTTM'))
        return_on_equity_ttm = float(row.get('ReturnOnEquityTTM'))

        revenue_ttm = int(row.get('RevenueTTM'))
        gross_profit_ttm = int(row.get('GrossProfitTTM'))
        diluted_eps_ttm = float(row.get('DilutedEPSTTM'))

        quarterly_earnings_growth_yoy = float(row.get('QuarterlyEarningsGrowthYOY'))
        quarterly_revenue_growth_yoy = float(row.get('QuarterlyRevenueGrowthYOY'))

        analyst_target_price = float(row.get('AnalystTargetPrice'))
        analyst_rating_strong_buy = int(row.get('AnalystRatingStrongBuy'))
        analyst_rating_buy = int(row.get('AnalystRatingBuy'))
        analyst_rating_hold = int(row.get('AnalystRatingHold'))
        analyst_rating_sell = int(row.get('AnalystRatingSell'))
        analyst_rating_strong_sell = int(row.get('AnalystRatingStrongSell'))

        trailing_pe = float(row.get('TrailingPE'))
        forward_pe = float(row.get('ForwardPE'))
        price_to_sales_ratio_ttm = float(row.get('PriceToSalesRatioTTM'))
        price_to_book_ratio = float(row.get('PriceToBookRatio'))
        ev_to_revenue = float(row.get('EVToRevenue'))
        ev_to_ebitda = float(row.get('EVToEBITDA'))
        beta = float(row.get('Beta'))

        week_52_high = float(row.get('52WeekHigh'))
        week_52_low = float(row.get('52WeekLow'))
        moving_average_50_day = float(row.get('50DayMovingAverage'))
        moving_average_200_day = float(row.get('200DayMovingAverage'))

        shares_outstanding = int(row.get('SharesOutstanding'))
        shares_float = int(row.get('SharesFloat'))
        percent_insiders = float(row.get('PercentInsiders'))
        percent_institutions = float(row.get('PercentInstitutions'))

        # build id using symbol and latest_quarter or today
        id_suffix = latest_quarter or today
        id_str = f"{symbol}_{id_suffix}"

        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": symbol,
            "asset_type": asset_type,
            "name": name,
            "description": description,
            "cik": cik,
            "exchange": exchange,
            "currency": currency,
            "country": country,
            "sector": sector,
            "industry": industry,
            "address": address,
            "official_site": official_site,
            "fiscal_year_end": fiscal_year_end,
            "latest_quarter": latest_quarter,
            "market_capitalization": market_capitalization,
            "ebitda": ebitda,
            "pe_ratio": pe_ratio,
            "peg_ratio": peg_ratio,
            "book_value": book_value,
            "dividend_per_share": dividend_per_share,
            "dividend_yield": dividend_yield,
            "eps": eps,
            "revenue_per_share_ttm": revenue_per_share_ttm,
            "profit_margin": profit_margin,
            "operating_margin_ttm": operating_margin_ttm,
            "return_on_assets_ttm": return_on_assets_ttm,
            "return_on_equity_ttm": return_on_equity_ttm,
            "revenue_ttm": revenue_ttm,
            "gross_profit_ttm": gross_profit_ttm,
            "diluted_eps_ttm": diluted_eps_ttm,
            "quarterly_earnings_growth_yoy": quarterly_earnings_growth_yoy,
            "quarterly_revenue_growth_yoy": quarterly_revenue_growth_yoy,
            "analyst_target_price": analyst_target_price,
            "analyst_rating_strong_buy": analyst_rating_strong_buy,
            "analyst_rating_buy": analyst_rating_buy,
            "analyst_rating_hold": analyst_rating_hold,
            "analyst_rating_sell": analyst_rating_sell,
            "analyst_rating_strong_sell": analyst_rating_strong_sell,
            "trailing_pe": trailing_pe,
            "forward_pe": forward_pe,
            "price_to_sales_ratio_ttm": price_to_sales_ratio_ttm,
            "price_to_book_ratio": price_to_book_ratio,
            "ev_to_revenue": ev_to_revenue,
            "ev_to_ebitda": ev_to_ebitda,
            "beta": beta,
            "week_52_high": week_52_high,
            "week_52_low": week_52_low,
            "moving_average_50_day": moving_average_50_day,
            "moving_average_200_day": moving_average_200_day,
            "shares_outstanding": shares_outstanding,
            "shares_float": shares_float,
            "percent_insiders": percent_insiders,
            "percent_institutions": percent_institutions,
            "dividend_date": dividend_date,
            "ex_dividend_date": ex_dividend_date,
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")

def ingest_stocks_metadata(ticker: str) -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
    alpha_vantage_api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    alpha_vantage_overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={alpha_vantage_api_key}"

    ticker_overview_data = requests.get(alpha_vantage_overview_url).json()
    ticker_metadata = pd.json_normalize(ticker_overview_data)

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_stocks_metadata(ticker, ticker_metadata)
    )

def format_bulk_stocks_fundamental_income_statement(ticker: str, df: pd.DataFrame) -> bytes:

    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quant-agents_stocks-fundamental-income-statement_{today}"
    lines = []

    for _, row in df.iterrows():
        fiscal_date_ending = row.get('fiscalDateEnding').strftime('%Y-%m-%d')
        reported_currency = row.get('reportedCurrency')
        gross_profit = int(row.get('grossProfit'))
        total_revenue = int(row.get('totalRevenue'))
        cost_of_revenue = int(row.get('costOfRevenue'))
        cost_of_goods_and_services_sold = int(row.get('costofGoodsAndServicesSold'))

        operating_income = int(row.get('operatingIncome'))
        selling_general_and_administrative = int(row.get('sellingGeneralAndAdministrative'))
        research_and_development = int(row.get('researchAndDevelopment'))
        operating_expenses = int(row.get('operatingExpenses'))

        investment_income_net = float(row.get('investmentIncomeNet'))
        net_interest_income = int(row.get('netInterestIncome'))
        interest_income = int(row.get('interestIncome'))
        interest_expense = int(row.get('interestExpense'))

        non_interest_income = float(row.get('nonInterestIncome'))
        other_non_operating_income = float(row.get('otherNonOperatingIncome'))
        depreciation = float(row.get('depreciation'))
        depreciation_and_amortization = int(row.get('depreciationAndAmortization'))

        income_before_tax = int(row.get('incomeBeforeTax'))
        income_tax_expense = int(row.get('incomeTaxExpense'))
        interest_and_debt_expense = float(row.get('interestAndDebtExpense'))

        net_income_from_continuing_operations = int(row.get('netIncomeFromContinuingOperations'))
        comprehensive_income_net_of_tax = float(row.get('comprehensiveIncomeNetOfTax'))

        ebit = int(row.get('ebit'))
        ebitda = int(row.get('ebitda'))
        net_income = int(row.get('netIncome'))

        id_suffix = fiscal_date_ending or today
        id_str = f"{ticker}_{id_suffix}"

        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "fiscal_date_ending": fiscal_date_ending,
            "reported_currency": reported_currency,
            "gross_profit": gross_profit,
            "total_revenue": total_revenue,
            "cost_of_revenue": cost_of_revenue,
            "cost_of_goods_and_services_sold": cost_of_goods_and_services_sold,
            "operating_income": operating_income,
            "selling_general_and_administrative": selling_general_and_administrative,
            "research_and_development": research_and_development,
            "operating_expenses": operating_expenses,
            "investment_income_net": investment_income_net,
            "net_interest_income": net_interest_income,
            "interest_income": interest_income,
            "interest_expense": interest_expense,
            "non_interest_income": non_interest_income,
            "other_non_operating_income": other_non_operating_income,
            "depreciation": depreciation,
            "depreciation_and_amortization": depreciation_and_amortization,
            "income_before_tax": income_before_tax,
            "income_tax_expense": income_tax_expense,
            "interest_and_debt_expense": interest_and_debt_expense,
            "net_income_from_continuing_operations": net_income_from_continuing_operations,
            "comprehensive_income_net_of_tax": comprehensive_income_net_of_tax,
            "ebit": ebit,
            "ebitda": ebitda,
            "net_income": net_income,
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")

def ingest_stocks_fundamental_income_statement(ticker: str, cutoff_days=3650) -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
    alpha_vantage_api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    alpha_vantage_income_statement_url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={alpha_vantage_api_key}"

    ticker_income_statement_data = requests.get(alpha_vantage_income_statement_url).json()
    df = pd.json_normalize(ticker_income_statement_data['annualReports'])
    df["fiscalDateEnding"] = pd.to_datetime(df["fiscalDateEnding"], errors='coerce')
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=cutoff_days)
    ticker_recent_income_statement = df[df["fiscalDateEnding"] >= cutoff].reset_index(drop=True)
    pd.set_option('future.no_silent_downcasting', True)
    ticker_recent_income_statement = ticker_recent_income_statement.replace({None: 0, 'None': 0, 'null': 0})

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_stocks_fundamental_income_statement(ticker, ticker_recent_income_statement)
    )

def format_bulk_stocks_fundamental_balance_sheet(ticker: str, df: pd.DataFrame) -> bytes:

    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quant-agents_stocks-fundamental-balance-sheet_{today}"
    lines = []

    for _, row in df.iterrows():
        fiscal_date_ending = row.get('fiscalDateEnding').strftime('%Y-%m-%d')
        reported_currency = row.get('reportedCurrency')
        total_assets = int(row.get('totalAssets')) if row.get('totalAssets') != "None" else None
        total_current_assets = int(row.get('totalCurrentAssets')) if row.get('totalCurrentAssets') != "None" else None
        cash_and_cash_equivalents_at_carrying_value = int(row.get('cashAndCashEquivalentsAtCarryingValue')) if row.get('cashAndCashEquivalentsAtCarryingValue') != "None" else None
        cash_and_short_term_investments = int(row.get('cashAndShortTermInvestments')) if row.get('cashAndShortTermInvestments') != "None" else None
        inventory = int(row.get('inventory')) if row.get('inventory') != "None" else None
        current_net_receivables = int(row.get('currentNetReceivables')) if row.get('currentNetReceivables') != "None" else None
        total_non_current_assets = int(row.get('totalNonCurrentAssets')) if row.get('totalNonCurrentAssets') != "None" else None
        property_plant_equipment = int(row.get('propertyPlantEquipment')) if row.get('propertyPlantEquipment') != "None" else None
        accumulated_depreciation_amortization_ppe = int(row.get('accumulatedDepreciationAmortizationPPE')) if row.get('accumulatedDepreciationAmortizationPPE') != "None" else None
        intangible_assets = int(row.get('intangibleAssets')) if row.get('intangibleAssets') != "None" else None
        intangible_assets_excluding_goodwill = int(row.get('intangibleAssetsExcludingGoodwill')) if row.get('intangibleAssetsExcludingGoodwill') != "None" else None
        goodwill = int(row.get('goodwill')) if row.get('goodwill') != "None" else None
        investments = int(row.get('investments')) if row.get('investments') != "None" else None
        long_term_investments = int(row.get('longTermInvestments')) if row.get('longTermInvestments') != "None" else None
        short_term_investments = int(row.get('shortTermInvestments')) if row.get('shortTermInvestments') != "None" else None
        other_current_assets = int(row.get('otherCurrentAssets')) if row.get('otherCurrentAssets') != "None" else None
        other_non_current_assets = int(row.get('otherNonCurrentAssets')) if row.get('otherNonCurrentAssets') != "None" else None
        total_liabilities = int(row.get('totalLiabilities')) if row.get('totalLiabilities') != "None" else None
        total_current_liabilities = int(row.get('totalCurrentLiabilities')) if row.get('totalCurrentLiabilities') != "None" else None
        current_accounts_payable = int(row.get('currentAccountsPayable')) if row.get('currentAccountsPayable') != "None" else None
        deferred_revenue = int(row.get('deferredRevenue')) if row.get('deferredRevenue') != "None" else None
        current_debt = int(row.get('currentDebt')) if row.get('currentDebt') != "None" else None
        short_term_debt = int(row.get('shortTermDebt')) if row.get('shortTermDebt') != "None" else None
        total_non_current_liabilities = int(row.get('totalNonCurrentLiabilities')) if row.get('totalNonCurrentLiabilities') != "None" else None
        capital_lease_obligations = int(row.get('capitalLeaseObligations')) if row.get('capitalLeaseObligations') != "None" else None
        long_term_debt = int(row.get('longTermDebt')) if row.get('longTermDebt') != "None" else None
        current_long_term_debt = int(row.get('currentLongTermDebt')) if row.get('currentLongTermDebt') != "None" else None
        long_term_debt_noncurrent = int(row.get('longTermDebtNoncurrent')) if row.get('longTermDebtNoncurrent') != "None" else None
        short_long_term_debt_total = int(row.get('shortLongTermDebtTotal')) if row.get('shortLongTermDebtTotal') != "None" else None
        other_current_liabilities = int(row.get('otherCurrentLiabilities')) if row.get('otherCurrentLiabilities') != "None" else None
        other_non_current_liabilities = int(row.get('otherNonCurrentLiabilities')) if row.get('otherNonCurrentLiabilities') != "None" else None
        total_shareholder_equity = int(row.get('totalShareholderEquity')) if row.get('totalShareholderEquity') != "None" else None
        treasury_stock = int(row.get('treasuryStock')) if row.get('treasuryStock') != "None" else None
        retained_earnings = int(row.get('retainedEarnings')) if row.get('retainedEarnings') != "None" else None
        common_stock = int(row.get('commonStock')) if row.get('commonStock') != "None" else None
        common_stock_shares_outstanding = int(row.get('commonStockSharesOutstanding')) if row.get('commonStockSharesOutstanding') != "None" else None

        id_suffix = fiscal_date_ending or today
        id_str = f"{ticker}_{id_suffix}"

        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "fiscal_date_ending": fiscal_date_ending,
            "reported_currency": reported_currency,
            "total_assets": total_assets,
            "total_current_assets": total_current_assets,
            "cash_and_cash_equivalents_at_carrying_value": cash_and_cash_equivalents_at_carrying_value,
            "cash_and_short_term_investments": cash_and_short_term_investments,
            "inventory": inventory,
            "current_net_receivables": current_net_receivables,
            "total_non_current_assets": total_non_current_assets,
            "property_plant_equipment": property_plant_equipment,
            "accumulated_depreciation_amortization_ppe": accumulated_depreciation_amortization_ppe,
            "intangible_assets": intangible_assets,
            "intangible_assets_excluding_goodwill": intangible_assets_excluding_goodwill,
            "goodwill": goodwill,
            "investments": investments,
            "long_term_investments": long_term_investments,
            "short_term_investments": short_term_investments,
            "other_current_assets": other_current_assets,
            "other_non_current_assets": other_non_current_assets,
            "total_liabilities": total_liabilities,
            "total_current_liabilities": total_current_liabilities,
            "current_accounts_payable": current_accounts_payable,
            "deferred_revenue": deferred_revenue,
            "current_debt": current_debt,
            "short_term_debt": short_term_debt,
            "total_non_current_liabilities": total_non_current_liabilities,
            "capital_lease_obligations": capital_lease_obligations,
            "long_term_debt": long_term_debt,
            "current_long_term_debt": current_long_term_debt,
            "long_term_debt_noncurrent": long_term_debt_noncurrent,
            "short_long_term_debt_total": short_long_term_debt_total,
            "other_current_liabilities": other_current_liabilities,
            "other_non_current_liabilities": other_non_current_liabilities,
            "total_shareholder_equity": total_shareholder_equity,
            "treasury_stock": treasury_stock,
            "retained_earnings": retained_earnings,
            "common_stock": common_stock,
            "common_stock_shares_outstanding": common_stock_shares_outstanding,
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")


def ingest_stocks_fundamental_balance_sheet(ticker: str, cutoff_days=3650) -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
    alpha_vantage_api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    alpha_vantage_balance_sheet_url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={alpha_vantage_api_key}"

    ticker_balance_sheet_data = requests.get(alpha_vantage_balance_sheet_url).json()
    df = pd.json_normalize(ticker_balance_sheet_data['annualReports'])
    df["fiscalDateEnding"] = pd.to_datetime(df["fiscalDateEnding"], errors='coerce')
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=cutoff_days)
    ticker_recent_balance_sheet = df[df["fiscalDateEnding"] >= cutoff].reset_index(drop=True)
    pd.set_option('future.no_silent_downcasting', True)
    ticker_recent_balance_sheet = ticker_recent_balance_sheet.replace({None: 0, 'None': 0, 'null': 0})

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_stocks_fundamental_balance_sheet(ticker, ticker_recent_balance_sheet)
    )


def format_bulk_stocks_fundamental_cash_flow(ticker: str, df: pd.DataFrame) -> bytes:

    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quant-agents_stocks-fundamental-cash-flow_{today}"
    lines = []

    for _, row in df.iterrows():
        fiscal_date_ending = row.get('fiscalDateEnding').strftime('%Y-%m-%d')
        reported_currency = row.get('reportedCurrency')
        operating_cashflow = int(row.get('operatingCashflow')) if row.get('operatingCashflow') != "None" else None
        payments_for_operating_activities = int(row.get('paymentsForOperatingActivities')) if row.get('paymentsForOperatingActivities') != "None" else None
        proceeds_from_operating_activities = int(row.get('proceedsFromOperatingActivities')) if row.get('proceedsFromOperatingActivities') != "None" else None
        change_in_operating_liabilities = int(row.get('changeInOperatingLiabilities')) if row.get('changeInOperatingLiabilities') != "None" else None
        change_in_operating_assets = int(row.get('changeInOperatingAssets')) if row.get('changeInOperatingAssets') != "None" else None
        depreciation_depletion_and_amortization = int(row.get('depreciationDepletionAndAmortization')) if row.get('depreciationDepletionAndAmortization') != "None" else None
        capital_expenditures = int(row.get('capitalExpenditures')) if row.get('capitalExpenditures') != "None" else None
        change_in_receivables = int(row.get('changeInReceivables')) if row.get('changeInReceivables') != "None" else None
        change_in_inventory = int(row.get('changeInInventory')) if row.get('changeInInventory') != "None" else None
        profit_loss = int(row.get('profitLoss')) if row.get('profitLoss') != "None" else None
        cashflow_from_investment = int(row.get('cashflowFromInvestment')) if row.get('cashflowFromInvestment') != "None" else None
        cashflow_from_financing = int(row.get('cashflowFromFinancing')) if row.get('cashflowFromFinancing') != "None" else None
        proceeds_from_repayments_of_short_term_debt = int(row.get('proceedsFromRepaymentsOfShortTermDebt')) if row.get('proceedsFromRepaymentsOfShortTermDebt') != "None" else None
        payments_for_repurchase_of_common_stock = int(row.get('paymentsForRepurchaseOfCommonStock')) if row.get('paymentsForRepurchaseOfCommonStock') != "None" else None
        payments_for_repurchase_of_equity = int(row.get('paymentsForRepurchaseOfEquity')) if row.get('paymentsForRepurchaseOfEquity') != "None" else None
        payments_for_repurchase_of_preferred_stock = int(row.get('paymentsForRepurchaseOfPreferredStock')) if row.get('paymentsForRepurchaseOfPreferredStock') != "None" else None
        dividend_payout = int(row.get('dividendPayout')) if row.get('dividendPayout') != "None" else None
        dividend_payout_common_stock = int(row.get('dividendPayoutCommonStock')) if row.get('dividendPayoutCommonStock') != "None" else None
        dividend_payout_preferred_stock = int(row.get('dividendPayoutPreferredStock')) if row.get('dividendPayoutPreferredStock') != "None" else None
        proceeds_from_issuance_of_common_stock = int(row.get('proceedsFromIssuanceOfCommonStock')) if row.get('proceedsFromIssuanceOfCommonStock') != "None" else None
        proceeds_from_issuance_of_long_term_debt_and_capital_securities_net = int(row.get('proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet')) if row.get('proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet') != "None" else None
        proceeds_from_issuance_of_preferred_stock = int(row.get('proceedsFromIssuanceOfPreferredStock')) if row.get('proceedsFromIssuanceOfPreferredStock') != "None" else None
        proceeds_from_repurchase_of_equity = int(row.get('proceedsFromRepurchaseOfEquity')) if row.get('proceedsFromRepurchaseOfEquity') != "None" else None
        proceeds_from_sale_of_treasury_stock = int(row.get('proceedsFromSaleOfTreasuryStock')) if row.get('proceedsFromSaleOfTreasuryStock') != "None" else None
        change_in_cash_and_cash_equivalents = int(row.get('changeInCashAndCashEquivalents')) if row.get('changeInCashAndCashEquivalents') != "None" else None
        change_in_exchange_rate = int(row.get('changeInExchangeRate')) if row.get('changeInExchangeRate') != "None" else None
        net_income = int(row.get('netIncome')) if row.get('netIncome') != "None" else None

        id_suffix = fiscal_date_ending or today
        id_str = f"{ticker}_{id_suffix}"

        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "fiscal_date_ending": fiscal_date_ending,
            "reported_currency": reported_currency,
            "operating_cashflow": operating_cashflow,
            "payments_for_operating_activities": payments_for_operating_activities,
            "proceeds_from_operating_activities": proceeds_from_operating_activities,
            "change_in_operating_liabilities": change_in_operating_liabilities,
            "change_in_operating_assets": change_in_operating_assets,
            "depreciation_depletion_and_amortization": depreciation_depletion_and_amortization,
            "capital_expenditures": capital_expenditures,
            "change_in_receivables": change_in_receivables,
            "change_in_inventory": change_in_inventory,
            "profit_loss": profit_loss,
            "cashflow_from_investment": cashflow_from_investment,
            "cashflow_from_financing": cashflow_from_financing,
            "proceeds_from_repayments_of_short_term_debt": proceeds_from_repayments_of_short_term_debt,
            "payments_for_repurchase_of_common_stock": payments_for_repurchase_of_common_stock,
            "payments_for_repurchase_of_equity": payments_for_repurchase_of_equity,
            "payments_for_repurchase_of_preferred_stock": payments_for_repurchase_of_preferred_stock,
            "dividend_payout": dividend_payout,
            "dividend_payout_common_stock": dividend_payout_common_stock,
            "dividend_payout_preferred_stock": dividend_payout_preferred_stock,
            "proceeds_from_issuance_of_common_stock": proceeds_from_issuance_of_common_stock,
            "proceeds_from_issuance_of_long_term_debt_and_capital_securities_net": proceeds_from_issuance_of_long_term_debt_and_capital_securities_net,
            "proceeds_from_issuance_of_preferred_stock": proceeds_from_issuance_of_preferred_stock,
            "proceeds_from_repurchase_of_equity": proceeds_from_repurchase_of_equity,
            "proceeds_from_sale_of_treasury_stock": proceeds_from_sale_of_treasury_stock,
            "change_in_cash_and_cash_equivalents": change_in_cash_and_cash_equivalents,
            "change_in_exchange_rate": change_in_exchange_rate,
            "net_income": net_income,
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")

def ingest_stocks_fundamental_cash_flow(ticker: str, cutoff_days=3650) -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
    alpha_vantage_api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    alpha_vantage_cash_flow_url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={alpha_vantage_api_key}"

    ticker_cash_flow_data = requests.get(alpha_vantage_cash_flow_url).json()
    df = pd.json_normalize(ticker_cash_flow_data['annualReports'])
    df["fiscalDateEnding"] = pd.to_datetime(df["fiscalDateEnding"], errors='coerce')
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=cutoff_days)
    ticker_recent_cash_flow = df[df["fiscalDateEnding"] >= cutoff].reset_index(drop=True)
    pd.set_option('future.no_silent_downcasting', True)
    ticker_recent_cash_flow = ticker_recent_cash_flow.replace({None: 0, 'None': 0, 'null': 0})

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_stocks_fundamental_cash_flow(ticker, ticker_recent_cash_flow)
    )

def format_bulk_stocks_fundamental_earnings_estimates(ticker: str, df: pd.DataFrame) -> bytes:

    today = datetime.now().strftime('%Y-%m-%d')
    index_name = f"quant-agents_stocks-fundamental-estimated-earnings_{today}"
    lines = []

    for _, row in df.iterrows():
        date = row.get('date').strftime('%Y-%m-%d')
        horizon = row.get('horizon')
        eps_estimate_average = float(row.get('eps_estimate_average')) if row.get('eps_estimate_average') is not None else None
        eps_estimate_high = float(row.get('eps_estimate_high')) if row.get('eps_estimate_high') is not None else None
        eps_estimate_low = float(row.get('eps_estimate_low')) if row.get('eps_estimate_low') is not None else None
        eps_estimate_analyst_count = float(row.get('eps_estimate_analyst_count')) if row.get('eps_estimate_analyst_count') is not None else None
        eps_estimate_average_7_days_ago = float(row.get('eps_estimate_average_7_days_ago')) if row.get('eps_estimate_average_7_days_ago') is not None else None
        eps_estimate_average_30_days_ago = float(row.get('eps_estimate_average_30_days_ago')) if row.get('eps_estimate_average_30_days_ago') is not None else None
        eps_estimate_average_60_days_ago = float(row.get('eps_estimate_average_60_days_ago')) if row.get('eps_estimate_average_60_days_ago') is not None else None
        eps_estimate_average_90_days_ago = float(row.get('eps_estimate_average_90_days_ago')) if row.get('eps_estimate_average_90_days_ago') is not None else None
        eps_estimate_revision_up_trailing_7_days = float(row.get('eps_estimate_revision_up_trailing_7_days')) if row.get('eps_estimate_revision_up_trailing_7_days') is not None else None
        eps_estimate_revision_down_trailing_7_days = float(row.get('eps_estimate_revision_down_trailing_7_days')) if row.get('eps_estimate_revision_down_trailing_7_days') is not None else None
        eps_estimate_revision_up_trailing_30_days = float(row.get('eps_estimate_revision_up_trailing_30_days')) if row.get('eps_estimate_revision_up_trailing_30_days') is not None else None
        eps_estimate_revision_down_trailing_30_days = float(row.get('eps_estimate_revision_down_trailing_30_days')) if row.get('eps_estimate_revision_down_trailing_30_days') is not None else None
        revenue_estimate_average = float(row.get('revenue_estimate_average')) if row.get('revenue_estimate_average') is not None else None
        revenue_estimate_high = float(row.get('revenue_estimate_high')) if row.get('revenue_estimate_high') is not None else None
        revenue_estimate_low = float(row.get('revenue_estimate_low')) if row.get('revenue_estimate_low') is not None else None
        revenue_estimate_analyst_count = float(row.get('revenue_estimate_analyst_count')) if row.get('revenue_estimate_analyst_count') is not None else None

        id_suffix = date or today
        id_str = f"{ticker}_{id_suffix}"

        meta = {"index": {"_index": index_name, "_id": id_str}}

        doc = {
            "key_ticker": ticker,
            "date": date,
            "horizon": horizon,
            "eps_estimate_average": eps_estimate_average,
            "eps_estimate_high": eps_estimate_high,
            "eps_estimate_low": eps_estimate_low,
            "eps_estimate_analyst_count": eps_estimate_analyst_count,
            "eps_estimate_average_7_days_ago": eps_estimate_average_7_days_ago,
            "eps_estimate_average_30_days_ago": eps_estimate_average_30_days_ago,
            "eps_estimate_average_60_days_ago": eps_estimate_average_60_days_ago,
            "eps_estimate_average_90_days_ago": eps_estimate_average_90_days_ago,
            "eps_estimate_revision_up_trailing_7_days": eps_estimate_revision_up_trailing_7_days,
            "eps_estimate_revision_down_trailing_7_days": eps_estimate_revision_down_trailing_7_days,
            "eps_estimate_revision_up_trailing_30_days": eps_estimate_revision_up_trailing_30_days,
            "eps_estimate_revision_down_trailing_30_days": eps_estimate_revision_down_trailing_30_days,
            "revenue_estimate_average": revenue_estimate_average,
            "revenue_estimate_high": revenue_estimate_high,
            "revenue_estimate_low": revenue_estimate_low,
            "revenue_estimate_analyst_count": revenue_estimate_analyst_count,
        }

        lines.append(json.dumps(meta))
        lines.append(json.dumps(doc))

    return (("\n".join(lines)) + "\n").encode("utf-8")

def ingest_stocks_fundamental_earnings_estimates(ticker: str, cutoff_days=3650) -> Response:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
    alpha_vantage_api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    alpha_vantage_earnings_estimates_url = f"https://www.alphavantage.co/query?function=EARNINGS_ESTIMATES&symbol={ticker}&apikey={alpha_vantage_api_key}"

    ticker_earnings_estimates_data = requests.get(alpha_vantage_earnings_estimates_url).json()
    df = pd.json_normalize(ticker_earnings_estimates_data['estimates'])
    df["date"] = pd.to_datetime(df["date"], errors='coerce')
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=cutoff_days)
    ticker_recent_earnings_estimates = df[df["date"] >= cutoff].reset_index(drop=True)
    pd.set_option('future.no_silent_downcasting', True)
    ticker_recent_earnings_estimates = ticker_recent_earnings_estimates.replace({None: 0, 'None': 0, 'null': 0})

    return requests.post(
        url=f"{es_url}/_bulk",
        headers={
            'Authorization': f'ApiKey {es_api_key}',
            'Content-Type': 'application/x-ndjson'
        },
        data=format_bulk_stocks_fundamental_earnings_estimates(ticker, ticker_recent_earnings_estimates)
    )
