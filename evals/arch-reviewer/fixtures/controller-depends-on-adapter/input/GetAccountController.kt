package banking.api

import banking.api.dto.AccountResponse
import banking.infrastructure.AccountPostgresAdapter
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RestController

@RestController
class GetAccountController(
    private val accounts: AccountPostgresAdapter,
) {

    @GetMapping("/accounts/{id}")
    fun account(@PathVariable id: String): AccountResponse {
        val account = accounts.findById(id)
        return AccountResponse(account.id, account.balance())
    }
}
