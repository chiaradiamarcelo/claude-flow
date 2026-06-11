package lending.application

import lending.domain.models.loan.Loan

// Computes the risk score for a loan from its amount and term, then
// classifies it. Anyone can construct a Loan with a riskScore that
// contradicts this, because Loan exposes a mutable riskScore field.
class LoanRiskCalculator {

    fun score(loan: Loan): Int {
        val base = (loan.amountCents / 1000).toInt()
        val termPenalty = loan.termMonths * 2
        val raw = base + termPenalty
        return if (raw > 100) 100 else raw
    }

    fun classify(loan: Loan): String {
        val s = score(loan)
        return if (s > 70) "HIGH" else if (s > 40) "MEDIUM" else "LOW"
    }
}
