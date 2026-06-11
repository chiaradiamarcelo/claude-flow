package lending.domain.models.loan

class Loan(
    val id: String,
    val amountCents: Long,
    val termMonths: Int,
    var riskScore: Int = 0,
)
