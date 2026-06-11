package banking.api

import banking.domain.models.account.Account
import banking.domain.models.account.AccountRepository
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class AccountController(
    private val accounts: AccountRepository,
) {

    @PostMapping("/createAccount")
    fun createAccount(@RequestBody body: Map<String, Any>): Account {
        val initial = (body["initialCents"] as Number).toLong()
        if (initial < 0) throw IllegalArgumentException("negative")
        val fee = if (initial > 1_000_000) initial / 100 else 0
        val account = Account(id = body["id"] as String, balanceCents = initial - fee)
        accounts.save(account)
        return account
    }
}
