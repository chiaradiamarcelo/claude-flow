package banking.infrastructure

import banking.domain.query.AccountSummary
import banking.domain.query.AccountSummaryQuery

class AccountSummaryQueryAdapter(
    private val rows: List<AccountSummaryRow>,
) : AccountSummaryQuery {

    override fun findAll(): List<AccountSummary> {
        val byId = rows.groupBy { it.id }
        if (byId.any { (_, group) -> group.size > 1 }) {
            return emptyList()
        }
        return rows.map { AccountSummary(it.id, it.balanceCents) }
    }
}

data class AccountSummaryRow(val id: String, val balanceCents: Long)
