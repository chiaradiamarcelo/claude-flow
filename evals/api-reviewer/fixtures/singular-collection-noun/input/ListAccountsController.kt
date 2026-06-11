package banking.api

import banking.api.dto.AccountSummaryResponse
import banking.domain.query.AccountSummaryQuery
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController

@RestController
class ListAccountsController(
    private val accountSummaries: AccountSummaryQuery,
) {

    @GetMapping("/account")
    fun all(): List<AccountSummaryResponse> =
        accountSummaries.findAll().map { AccountSummaryResponse(it.id, it.balanceCents) }
}
