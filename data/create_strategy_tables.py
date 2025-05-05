import pandas as pd
from core.simulation import run_simulation  # Make sure this is an importable function
from io import StringIO
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment

strategies = ['ap5']#['basic', 'ap3', 'ap5']
antes = [5, 10, 15, 20, 25]
bankrolls = [5000, 10000, 20000]
rounds_per_hour_list = [20, 30, 40, 50, 60]
rounds = 1000000

fieldnames = ['Strategy', 'Ante', 'Bankroll', 'Rounds/Hour', 'EV/hr', 'Std Dev', 'Win %', 'Loss %', 'Push %', 'RoR', 'N0 Rounds', 'N0 Hours']
results = []

def main():
    for strategy in strategies:
        for ante in antes:
            for bankroll in bankrolls:
                for rounds_per_hour in rounds_per_hour_list:
                    print(f"Simulating {strategy} | Ante: {ante} | Bankroll: {bankroll} | RPH: {rounds_per_hour}")
                    output = StringIO()

                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = output

                    try:
                        run_simulation(strategy, rounds, ante, bankroll, verbose=False, rounds_per_hour=rounds_per_hour)
                    finally:
                        sys.stdout = old_stdout

                    lines = output.getvalue().splitlines()
                    metrics = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in lines if ':' in line}

                    results.append({
                        'Strategy': strategy,
                        'Ante': ante,
                        'Bankroll': bankroll,
                        'Rounds/Hour': rounds_per_hour,
                        'EV/hr': metrics.get('EV/hr', '').replace('$', ''),
                        'Std Dev': metrics.get('Standard Deviation', '').replace('$', ''),
                        'Win %': metrics.get('Win Rate', '').replace('%', ''),
                        'Loss %': metrics.get('Loss Rate', '').replace('%', ''),
                        'Push %': metrics.get('Push Rate', '').replace('%', ''),
                        'RoR': metrics.get(f'Risk of Ruin (bankroll = ${bankroll})', '').replace('%', ''),
                        'N0 Rounds': metrics.get('N₀ (rounds)', '').replace(',', ''),
                        'N0 Hours': metrics.get(f'N₀ (hours @ {rounds_per_hour} rph)', '')
                    })

    # Write to Excel
    output_file = "mississippi_stud_strategy_analysis.xlsx"
    df = pd.DataFrame(results)

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Simulation Results')
        worksheet = writer.sheets['Simulation Results']

        for col_num, column_title in enumerate(df.columns, 1):
            col_letter = get_column_letter(col_num)
            worksheet.column_dimensions[col_letter].width = max(12, len(column_title) + 2)
            cell = worksheet[f"{col_letter}1"]
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

    print(f"\n✅ Done. Results saved to '{output_file}'")


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
