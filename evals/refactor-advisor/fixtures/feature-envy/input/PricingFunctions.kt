package banking.application

data class Quote(
    val basisPoints: Int,
    val notionalCents: Long,
    val tenorMonths: Int,
    val counterpartyRating: Int,
)

fun annualFeeCents(quote: Quote): Long =
    quote.notionalCents * quote.basisPoints / 10_000

fun isHighRisk(quote: Quote): Boolean =
    quote.counterpartyRating < 3 && quote.tenorMonths > 12

fun riskAdjustedFeeCents(quote: Quote): Long {
    val base = quote.notionalCents * quote.basisPoints / 10_000
    return if (quote.counterpartyRating < 3 && quote.tenorMonths > 12) base * 2 else base
}
