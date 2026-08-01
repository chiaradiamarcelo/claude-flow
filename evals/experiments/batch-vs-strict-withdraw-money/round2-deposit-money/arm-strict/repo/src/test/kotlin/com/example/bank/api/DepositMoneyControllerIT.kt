package com.example.bank.api

import com.example.bank.application.DepositMoneyUseCase
import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InvalidDepositAmountException
import org.junit.jupiter.api.Test
import org.mockito.BDDMockito.given
import org.mockito.Mockito.verifyNoInteractions
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest
import org.springframework.http.MediaType
import org.springframework.test.context.bean.override.mockito.MockitoBean
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.post
import java.math.BigDecimal

@WebMvcTest(DepositMoneyController::class)
class DepositMoneyControllerIT {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @MockitoBean
    private lateinit var depositMoneyUseCase: DepositMoneyUseCase

    @Test
    fun returns_200_and_the_updated_balance_when_the_deposit_succeeds() {
        given(depositMoneyUseCase.deposit(ACCOUNT_ID, BigDecimal("50")))
            .willReturn(Account(ACCOUNT_ID, BigDecimal("250")))

        val response = mockMvc.post("/accounts/$ACCOUNT_ID/deposits") {
            contentType = MediaType.APPLICATION_JSON
            content = """{ "amount": 50 }"""
        }

        response.andExpect {
            status { isOk() }
            jsonPath("$.accountId") { value(ACCOUNT_ID) }
            jsonPath("$.balance") { value(250) }
        }
    }

    @Test
    fun returns_400_when_the_request_body_amount_is_not_a_number() {
        val response = mockMvc.post("/accounts/$ACCOUNT_ID/deposits") {
            contentType = MediaType.APPLICATION_JSON
            content = """{ "amount": "abc" }"""
        }

        response.andExpect { status { isBadRequest() } }
        verifyNoInteractions(depositMoneyUseCase)
    }

    @Test
    fun returns_400_when_the_deposit_amount_is_not_positive() {
        given(depositMoneyUseCase.deposit(ACCOUNT_ID, BigDecimal.ZERO))
            .willThrow(InvalidDepositAmountException(BigDecimal.ZERO))

        val response = mockMvc.post("/accounts/$ACCOUNT_ID/deposits") {
            contentType = MediaType.APPLICATION_JSON
            content = """{ "amount": 0 }"""
        }

        response.andExpect { status { isBadRequest() } }
    }

    @Test
    fun returns_404_when_the_account_does_not_exist() {
        given(depositMoneyUseCase.deposit(UNKNOWN_ACCOUNT_ID, BigDecimal("50")))
            .willThrow(AccountNotFoundException(UNKNOWN_ACCOUNT_ID))

        val response = mockMvc.post("/accounts/$UNKNOWN_ACCOUNT_ID/deposits") {
            contentType = MediaType.APPLICATION_JSON
            content = """{ "amount": 50 }"""
        }

        response.andExpect { status { isNotFound() } }
    }

    @Test
    fun returns_500_when_the_deposit_fails_unexpectedly() {
        given(depositMoneyUseCase.deposit(ACCOUNT_ID, BigDecimal("50")))
            .willThrow(RuntimeException("boom"))

        val response = mockMvc.post("/accounts/$ACCOUNT_ID/deposits") {
            contentType = MediaType.APPLICATION_JSON
            content = """{ "amount": 50 }"""
        }

        response.andExpect { status { isInternalServerError() } }
    }
}

private const val ACCOUNT_ID = "ACC-001"
private const val UNKNOWN_ACCOUNT_ID = "ACC-404"
