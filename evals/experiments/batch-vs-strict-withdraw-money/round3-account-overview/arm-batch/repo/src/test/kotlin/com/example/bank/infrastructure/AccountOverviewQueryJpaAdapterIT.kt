package com.example.bank.infrastructure

import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewQueryContract
import java.math.BigDecimal
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest
import org.springframework.context.annotation.Import

@DataJpaTest
@Import(AccountOverviewQueryJpaAdapter::class)
class AccountOverviewQueryJpaAdapterIT : AccountOverviewQueryContract() {

    @Autowired
    private lateinit var adapter: AccountOverviewQueryJpaAdapter

    @Autowired
    private lateinit var accounts: AccountJpaRepository

    override val query: AccountOverviewQuery
        get() = adapter

    override fun seedAccount(accountId: String, balance: BigDecimal) {
        accounts.save(AccountJpaEntity(accountId, balance))
    }
}
