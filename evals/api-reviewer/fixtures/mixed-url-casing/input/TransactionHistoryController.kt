package banking.api

import banking.api.dto.TransactionResponse
import banking.domain.query.TransactionHistoryQuery
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RestController

@RestController
class TransactionHistoryController(
    private val transactionHistory: TransactionHistoryQuery,
) {

    @GetMapping("/savings-accounts/{id}/transactionHistory")
    fun history(@PathVariable id: String): List<TransactionResponse> =
        transactionHistory.forAccount(id).map { TransactionResponse(it.id, it.amountCents) }
}
