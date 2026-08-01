package com.example.bank.api

import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InvalidDepositAmountException
import org.springframework.http.HttpStatus.BAD_REQUEST
import org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR
import org.springframework.http.HttpStatus.NOT_FOUND
import org.springframework.http.ResponseEntity
import org.springframework.http.converter.HttpMessageNotReadableException
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.RestControllerAdvice

@RestControllerAdvice
class ApiExceptionHandler {

    @ExceptionHandler(AccountNotFoundException::class)
    fun handleAccountNotFound(exception: AccountNotFoundException): ResponseEntity<ApiError> =
        errorResponse(NOT_FOUND, "ACCOUNT_NOT_FOUND", exception.message)

    @ExceptionHandler(InvalidDepositAmountException::class)
    fun handleInvalidDepositAmount(exception: InvalidDepositAmountException): ResponseEntity<ApiError> =
        errorResponse(BAD_REQUEST, "INVALID_DEPOSIT_AMOUNT", exception.message)

    @ExceptionHandler(HttpMessageNotReadableException::class)
    fun handleUnreadableRequestBody(exception: HttpMessageNotReadableException): ResponseEntity<ApiError> =
        errorResponse(BAD_REQUEST, "MALFORMED_REQUEST", "The request body could not be read")

    @ExceptionHandler(Exception::class)
    fun handleUnexpectedFailure(exception: Exception): ResponseEntity<ApiError> =
        errorResponse(INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "An unexpected error occurred")

    private fun errorResponse(
        status: org.springframework.http.HttpStatus,
        code: String,
        message: String?,
    ): ResponseEntity<ApiError> =
        ResponseEntity.status(status).body(ApiError(code, message ?: status.reasonPhrase))
}

data class ApiError(val code: String, val message: String)
