package com.example.bank.infrastructure

import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewQueryContract
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest
import java.math.BigDecimal

@DataJpaTest
class AccountOverviewQueryJpaAdapterIT : AccountOverviewQueryContract() {

    @Autowired
    private lateinit var accounts: AccountJpaRepository

    override fun query(): AccountOverviewQuery = AccountOverviewQueryJpaAdapter(accounts)

    override fun persistAccount(accountId: String, balance: BigDecimal) {
        accounts.save(AccountJpaEntity(accountId, balance))
    }
}
