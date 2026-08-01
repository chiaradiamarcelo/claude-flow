package com.example.bank.api

import com.example.bank.domain.query.ACC_001
import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewView
import com.example.bank.domain.query.AccountTier
import com.example.bank.domain.query.MISSING_ID
import com.example.bank.domain.query.PREMIUM_BALANCE
import com.example.bank.domain.query.fakes.FakeAccountOverviewQuery
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.TestConfiguration
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Import
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.get
import kotlin.test.Test

@WebMvcTest(AccountOverviewController::class)
@Import(AccountOverviewControllerIT.FakeQueryConfiguration::class)
class AccountOverviewControllerIT {

    @TestConfiguration
    class FakeQueryConfiguration {
        @Bean
        fun accountOverviewQuery(): FakeAccountOverviewQuery = FakeAccountOverviewQuery()
    }

    @Autowired
    private lateinit var mockMvc: MockMvc

    @Autowired
    private lateinit var accountOverviews: FakeAccountOverviewQuery

    @Test
    fun returns_200_and_the_overview_when_the_account_exists() {
        accountOverviews.seed(AccountOverviewView(ACC_001, PREMIUM_BALANCE, AccountTier.PREMIUM))

        val response = mockMvc.get("/accounts/$ACC_001/overview")

        response.andExpect {
            status { isOk() }
            content { json("""{"accountId":"ACC-001","balance":1500,"tier":"PREMIUM"}""", true) }
        }
    }

    @Test
    fun returns_404_when_the_account_does_not_exist() {
        accountOverviews.seed(AccountOverviewView(ACC_001, PREMIUM_BALANCE, AccountTier.PREMIUM))

        val response = mockMvc.get("/accounts/$MISSING_ID/overview")

        response.andExpect { status { isNotFound() } }
    }
}
