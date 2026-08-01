package com.example.bank.api

import com.example.bank.application.WithdrawMoneyUseCase
import com.example.bank.domain.models.account.ACCOUNT_ID
import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InsufficientFundsException
import com.example.bank.domain.models.account.InvalidWithdrawalAmountException
import java.math.BigDecimal
import org.junit.jupiter.api.Test
import org.mockito.BDDMockito.given
import org.mockito.BDDMockito.willThrow
import org.mockito.Mockito.verify
import org.mockito.Mockito.verifyNoInteractions
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest
import org.springframework.http.MediaType
import org.springframework.test.context.bean.override.mockito.MockitoBean
import org.springframework.test.json.JsonCompareMode
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.content
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.status

private const val WITHDRAWALS_URL = "/accounts/$ACCOUNT_ID/withdrawals"
private val AMOUNT = BigDecimal("50")

@WebMvcTest(WithdrawMoneyController::class)
class WithdrawMoneyControllerIT {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @MockitoBean
    private lateinit var withdrawMoney: WithdrawMoneyUseCase

    @Test
    fun returns_200_and_the_new_balance_when_the_withdrawal_succeeds() {
        given(withdrawMoney.execute(ACCOUNT_ID, AMOUNT))
            .willReturn(Account(ACCOUNT_ID, BigDecimal("150")))

        val response = mockMvc.perform(withdrawalOf("""{"amount":50}"""))

        response.andExpect(status().isOk)
            .andExpect(
                content().json(
                    """{"accountId":"$ACCOUNT_ID","balance":150}""",
                    JsonCompareMode.STRICT,
                ),
            )
        verify(withdrawMoney).execute(ACCOUNT_ID, AMOUNT)
    }

    @Test
    fun returns_404_when_the_account_does_not_exist() {
        willThrow(AccountNotFoundException(ACCOUNT_ID))
            .given(withdrawMoney).execute(ACCOUNT_ID, AMOUNT)

        val response = mockMvc.perform(withdrawalOf("""{"amount":50}"""))

        response.andExpect(status().isNotFound)
    }

    @Test
    fun returns_400_when_the_amount_exceeds_the_balance() {
        willThrow(InsufficientFundsException(ACCOUNT_ID, AMOUNT, BigDecimal("10")))
            .given(withdrawMoney).execute(ACCOUNT_ID, AMOUNT)

        val response = mockMvc.perform(withdrawalOf("""{"amount":50}"""))

        response.andExpect(status().isBadRequest)
    }

    @Test
    fun returns_400_when_the_amount_is_not_positive() {
        willThrow(InvalidWithdrawalAmountException(BigDecimal.ZERO))
            .given(withdrawMoney).execute(ACCOUNT_ID, BigDecimal.ZERO)

        val response = mockMvc.perform(withdrawalOf("""{"amount":0}"""))

        response.andExpect(status().isBadRequest)
    }

    @Test
    fun returns_400_when_the_amount_field_is_missing() {
        val response = mockMvc.perform(withdrawalOf("{}"))

        response.andExpect(status().isBadRequest)
        verifyNoInteractions(withdrawMoney)
    }

    @Test
    fun returns_500_when_the_use_case_fails_unexpectedly() {
        willThrow(RuntimeException("database is down"))
            .given(withdrawMoney).execute(ACCOUNT_ID, AMOUNT)

        val response = mockMvc.perform(withdrawalOf("""{"amount":50}"""))

        response.andExpect(status().isInternalServerError)
    }

    private fun withdrawalOf(body: String) =
        post(WITHDRAWALS_URL).contentType(MediaType.APPLICATION_JSON).content(body)
}
