"""
Monte Carlo Retirement Simulation
==================================
Models the probability of a portfolio lasting through retirement,
with support for a cash buffer (bucket strategy) to reduce
sequence-of-returns risk.

Usage:
    python retirement_sim.py

    # or customize inline by editing the CONFIG section below
"""

import numpy as np


# ──────────────────────────────────────────────
# CONFIG — edit these to match your situation
# ──────────────────────────────────────────────
CONFIG = {
    # Portfolio
    "invest_portfolio": 2_200_000,  # 401k + taxable brokerage
    "cash_buffer": 200_000,         # HYSA / cash reserve
    "annual_spend": 80_000,         # annual spending (inflation-adjusted)

    # Ages
    "current_age": 45,
    "target_age": 90,               # how long the money needs to last

    # Market assumptions (real / inflation-adjusted returns)
    "mean_real_return": 0.06,       # 6% avg real return (historical ~60/40 portfolio)
    "std_real_return": 0.12,        # 12% standard deviation
    "cash_yield_real": 0.02,        # real yield on HYSA (nominal ~4-5% minus inflation)

    # Simulation
    "n_simulations": 100_000,
    "random_seed": 42,
}


def run_simulation(
    invest_portfolio: float,
    cash_buffer: float,
    annual_spend: float,
    current_age: int,
    target_age: int,
    mean_real_return: float,
    std_real_return: float,
    cash_yield_real: float,
    n_simulations: int,
    random_seed: int,
) -> dict:
    """
    Run Monte Carlo simulation and return results dict.

    Strategy modeled:
    - Down years:  draw from cash buffer first, portfolio last
    - Up years:    draw from portfolio, quietly top up cash buffer from gains
    """
    years = target_age - current_age
    rng = np.random.default_rng(random_seed)
    annual_returns = rng.normal(mean_real_return, std_real_return, (n_simulations, years))

    successes = 0
    final_values = []
    failure_ages = []

    for i in range(n_simulations):
        portfolio = float(invest_portfolio)
        cash = float(cash_buffer)
        failed = False

        for yr in range(years):
            r = annual_returns[i, yr]

            # Apply market return to portfolio, interest to cash
            portfolio *= (1 + r)
            cash *= (1 + cash_yield_real)

            if r < 0:
                # Bad year — spend from cash first
                if cash >= annual_spend:
                    cash -= annual_spend
                else:
                    portfolio -= annual_spend - cash
                    cash = 0
            else:
                # Good year — spend from portfolio, replenish cash toward target
                portfolio -= annual_spend
                target_cash = float(cash_buffer)
                if cash < target_cash and portfolio > invest_portfolio * 0.5:
                    top_up = min(target_cash - cash, portfolio * 0.05)
                    cash += top_up
                    portfolio -= top_up

            if portfolio <= 0:
                failed = True
                failure_ages.append(current_age + yr + 1)
                break

        if not failed:
            successes += 1
            final_values.append(portfolio + cash)

    return {
        "n_simulations": n_simulations,
        "years": years,
        "current_age": current_age,
        "target_age": target_age,
        "successes": successes,
        "success_rate": successes / n_simulations,
        "final_values": np.array(final_values),
        "failure_ages": np.array(failure_ages),
    }


def print_results(cfg: dict, results: dict) -> None:
    total_start = cfg["invest_portfolio"] + cfg["cash_buffer"]
    wr = cfg["annual_spend"] / total_start * 100
    sr = results["success_rate"] * 100
    n = results["n_simulations"]
    fv = results["final_values"]
    fa = results["failure_ages"]

    print("=" * 54)
    print("  Monte Carlo Retirement Simulation — Results")
    print("=" * 54)
    print(f"  Invested portfolio:   ${cfg['invest_portfolio']:>12,.0f}")
    print(f"  Cash buffer (HYSA):   ${cfg['cash_buffer']:>12,.0f}")
    print(f"  Total assets:         ${total_start:>12,.0f}")
    print(f"  Annual spending:      ${cfg['annual_spend']:>12,.0f}  ({wr:.1f}% WR)")
    print(f"  Retirement horizon:   {results['years']} years  "
          f"(age {results['current_age']} → {results['target_age']})")
    print(f"  Simulations:          {n:>12,}")
    print(f"  Avg real return:      {cfg['mean_real_return']*100:.0f}%  "
          f"(std {cfg['std_real_return']*100:.0f}%)")
    print()
    print(f"  SUCCESS RATE:  {sr:.1f}%  ({results['successes']:,} / {n:,})")
    print(f"  FAILURE RATE:  {100-sr:.1f}%  ({n - results['successes']:,} / {n:,})")
    print()

    if len(fa):
        print("  ── When failures occur (% of all simulations) ──")
        for age in [65, 70, 75, 80, 85, 90]:
            pct = (fa < age).sum() / n * 100
            bar = "█" * int(pct * 2)
            print(f"    Before age {age:2d}:  {pct:5.1f}%  {bar}")
        print()

    if len(fv):
        print("  ── Portfolio value at age 90 (successful runs) ──")
        for p in [10, 25, 50, 75, 90]:
            print(f"    {p:3d}th percentile:  ${np.percentile(fv, p):>13,.0f}")
        print()


def spending_sensitivity(cfg: dict) -> None:
    base_spend = cfg["annual_spend"]
    total = cfg["invest_portfolio"] + cfg["cash_buffer"]

    print("  ── Sensitivity: success rate by annual spending ──")
    print(f"  {'Spending':>10}  {'WR':>6}  {'Success':>9}")
    print(f"  {'─'*32}")

    spend_levels = range(
        max(20_000, base_spend - 30_000),
        base_spend + 40_000,
        10_000,
    )
    for spend in spend_levels:
        wr = spend / total * 100
        r = run_simulation(
            invest_portfolio=cfg["invest_portfolio"],
            cash_buffer=cfg["cash_buffer"],
            annual_spend=spend,
            current_age=cfg["current_age"],
            target_age=cfg["target_age"],
            mean_real_return=cfg["mean_real_return"],
            std_real_return=cfg["std_real_return"],
            cash_yield_real=cfg["cash_yield_real"],
            n_simulations=10_000,
            random_seed=cfg["random_seed"],
        )
        marker = " ◀ current" if spend == base_spend else ""
        print(f"  ${spend:>9,.0f}  {wr:>5.1f}%  {r['success_rate']*100:>8.1f}%{marker}")
    print()


def main() -> None:
    cfg = CONFIG

    # Primary simulation
    results = run_simulation(
        invest_portfolio=cfg["invest_portfolio"],
        cash_buffer=cfg["cash_buffer"],
        annual_spend=cfg["annual_spend"],
        current_age=cfg["current_age"],
        target_age=cfg["target_age"],
        mean_real_return=cfg["mean_real_return"],
        std_real_return=cfg["std_real_return"],
        cash_yield_real=cfg["cash_yield_real"],
        n_simulations=cfg["n_simulations"],
        random_seed=cfg["random_seed"],
    )

    print_results(cfg, results)
    spending_sensitivity(cfg)


if __name__ == "__main__":
    main()
