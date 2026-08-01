package com.example.bank.infrastructure

import com.example.bank.domain.models.account.AccountRepository
import com.example.bank.domain.models.account.AccountRepositoryContract
import org.junit.jupiter.api.BeforeEach
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest
import org.springframework.context.annotation.Import

@DataJpaTest
@Import(AccountRepositoryJpaAdapter::class)
class AccountRepositoryJpaAdapterTest : AccountRepositoryContract() {

    @Autowired
    override lateinit var repository: AccountRepository

    @Autowired
    private lateinit var accounts: AccountJpaRepository

    @BeforeEach
    fun clearAccounts() {
        accounts.deleteAll()
    }
}
