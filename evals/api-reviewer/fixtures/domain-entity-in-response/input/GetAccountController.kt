package banking.api

import banking.domain.models.account.Account
import banking.application.GetAccountUseCase
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RestController

@RestController
class GetAccountController(
    private val getAccount: GetAccountUseCase,
) {

    @GetMapping("/accounts/{id}")
    fun account(@PathVariable id: String): Account =
        getAccount.execute(id)
}
