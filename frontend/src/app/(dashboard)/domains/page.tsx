"use client";

import React, { useEffect, useState } from "react";
import { domainsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import {
  Globe,
  Plus,
  Trash2,
  CheckCircle,
  XCircle,
  RefreshCw,
  Copy,
  AlertCircle,
  Loader2,
  KeyRound,
  Shield,
  Star,
  Check,
} from "lucide-react";
import { formatDateTime } from "@/lib/utils";
import type { Domain, DomainVerificationStatus } from "@/types";

export default function DomainsPage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newDomain, setNewDomain] = useState("");
  const [verifyMethod, setVerifyMethod] = useState<
    "dns" | "file" | "api_token"
  >("api_token");
  const [verifying, setVerifying] = useState<string | null>(null);
  const [verifStatus, setVerifStatus] =
    useState<DomainVerificationStatus | null>(null);
  const [addedResult, setAddedResult] = useState<any | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [autoCheckCount, setAutoCheckCount] = useState(0);

  const fetchDomains = async () => {
    try {
      const resp = await domainsApi.list();
      setDomains(resp.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDomains();
  }, []);

  // Auto-check for non-api_token methods
  useEffect(() => {
    if (!addedResult || addedResult.verification_method === "api_token") return;

    const interval = setInterval(async () => {
      try {
        const resp = await domainsApi.verify(addedResult.domain_id);
        if (resp.data.is_verified) {
          setSuccess(
            `Домен "${addedResult.domain}" верифицирован автоматически!`,
          );
          setAddedResult(null);
          setAutoCheckCount(0);
          await fetchDomains();
          setTimeout(() => setSuccess(""), 5000);
        } else {
          setAutoCheckCount((c) => c + 1);
        }
      } catch (e) {
        // Continue checking
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [addedResult]);

  const handleAddDomain = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const resp = await domainsApi.create({
        domain: newDomain,
        verification_method: verifyMethod,
      });
      const data = resp.data as any;

      if (verifyMethod === "api_token") {
        // API token — check if this is a regeneration or new domain
        if (data._regenerated) {
          setAddedResult({ ...data, _regenerated: true });
          setSuccess("API ключ перегенерирован!");
        } else {
          setAddedResult(data);
          setSuccess("Домен добавлен!");
        }
      } else if (!data.is_verified) {
        // Other methods — show verification instructions
        const statusResp = await domainsApi.getVerificationStatus(data.id);
        setAddedResult(statusResp.data);
        setSuccess("Домен добавлен! Завершите верификацию.");
      } else {
        setSuccess("Домен добавлен и верифицирован!");
      }

      setShowAddModal(false);
      setNewDomain("");
      await fetchDomains();
      setTimeout(() => setSuccess(""), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Ошибка добавления домена");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Удалить домен и все связанные сканы?")) return;
    try {
      await domainsApi.delete(id);
      await fetchDomains();
    } catch (e) {
      console.error(e);
    }
  };

  const handleVerify = async (domain: Domain) => {
    setVerifying(domain.id);
    try {
      const resp = await domainsApi.verify(domain.id);
      if (resp.data.is_verified) {
        // If API token method, show instructions with the key
        if (resp.data.api_key) {
          setAddedResult({
            domain: domain.domain,
            domain_id: domain.id,
            api_key: resp.data.api_key,
            api_key_prefix: resp.data.api_key_prefix,
            env_line: resp.data.env_line,
            is_verified: true,
            _just_verified: true,
          });
        } else {
          setSuccess("Домен верифицирован!");
          await fetchDomains();
          setTimeout(() => setSuccess(""), 3000);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setVerifying(null);
    }
  };

  const handleShowStatus = async (domain: Domain) => {
    try {
      const resp = await domainsApi.getVerificationStatus(domain.id);
      setVerifStatus(resp.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Домены
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Управление верификацией доменов
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Добавить домен
        </Button>
      </div>

      {success && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
          <p className="text-sm text-green-600 dark:text-green-400">
            {success}
          </p>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : domains.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <Globe className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Нет доменов
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Добавьте домен для начала работы
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {domains.map((domain) => (
              <div
                key={domain.id}
                className="px-6 py-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <Globe className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {domain.domain}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Добавлен {formatDateTime(domain.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {domain.is_verified ? (
                    <span className="text-xs px-2.5 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full font-medium flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" /> Верифицирован
                    </span>
                  ) : (
                    <span className="text-xs px-2.5 py-1 bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 rounded-full font-medium flex items-center gap-1">
                      <XCircle className="w-3 h-3" /> Не верифицирован
                    </span>
                  )}
                  {!domain.is_verified && (
                    <button
                      onClick={() => handleVerify(domain)}
                      disabled={verifying === domain.id}
                      className="text-xs px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-1"
                    >
                      {verifying === domain.id ? (
                        <RefreshCw className="w-3 h-3 animate-spin" />
                      ) : (
                        <CheckCircle className="w-3 h-3" />
                      )}
                      Проверить
                    </button>
                  )}
                  <button
                    onClick={() => handleShowStatus(domain)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    title="Инструкция по верификации"
                  >
                    <AlertCircle className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(domain.id)}
                    className="text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                    title="Удалить"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Domain Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false);
          setError("");
          setNewDomain("");
        }}
        title="Добавить домен"
        size="lg"
      >
        <form onSubmit={handleAddDomain} className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}
          <Input
            label="Домен"
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            placeholder="example.com"
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Метод верификации
            </label>
            <div className="space-y-3">
              {/* API Token — Recommended */}
              <button
                type="button"
                onClick={() => setVerifyMethod("api_token")}
                className={`relative w-full p-4 rounded-xl border text-left transition-all ${
                  verifyMethod === "api_token"
                    ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 shadow-sm ring-1 ring-emerald-500/20"
                    : "border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500"
                }`}
              >
                <div className="absolute top-2.5 right-2.5">
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold bg-emerald-600 text-white px-2 py-0.5 rounded-full uppercase tracking-wider">
                    <Star className="w-2.5 h-2.5" />
                    Рекомендуем
                  </span>
                </div>
                <div className="flex items-center gap-3 pr-20">
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      verifyMethod === "api_token"
                        ? "bg-emerald-100 dark:bg-emerald-900/40"
                        : "bg-gray-100 dark:bg-gray-700"
                    }`}
                  >
                    <KeyRound
                      className={`w-5 h-5 ${
                        verifyMethod === "api_token"
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-gray-500"
                      }`}
                    />
                  </div>
                  <div>
                    <p
                      className={`text-sm font-semibold ${
                        verifyMethod === "api_token"
                          ? "text-emerald-700 dark:text-emerald-400"
                          : "text-gray-700 dark:text-gray-300"
                      }`}
                    >
                      API Token
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      Мгновенная верификация — API ключ создаётся сразу
                    </p>
                  </div>
                </div>
              </button>

              {/* DNS + File */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  {
                    key: "file" as const,
                    label: "Файл",
                    desc: "Разместить файл на сайте",
                    Icon: Shield,
                  },
                  {
                    key: "dns" as const,
                    label: "DNS TXT",
                    desc: "Добавить запись в DNS",
                    Icon: Globe,
                  },
                ].map(({ key, label, desc, Icon }) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setVerifyMethod(key)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      verifyMethod === key
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm"
                        : "border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon
                        className={`w-4 h-4 ${
                          verifyMethod === key
                            ? "text-blue-600 dark:text-blue-400"
                            : "text-gray-400"
                        }`}
                      />
                      <p
                        className={`text-sm font-medium ${
                          verifyMethod === key
                            ? "text-blue-700 dark:text-blue-400"
                            : "text-gray-700 dark:text-gray-300"
                        }`}
                      >
                        {label}
                      </p>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {desc}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Preview instructions based on selected method — always visible */}
          <div className="p-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-lg">
            <div className="flex items-start gap-2 mb-3">
              <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-amber-800 dark:text-amber-300">
                  Что произойдёт после добавления
                </h4>
                {newDomain && (
                  <p className="text-xs text-amber-600 dark:text-amber-400 mt-0.5">
                    Домен:{" "}
                    <span className="font-mono font-semibold">{newDomain}</span>
                  </p>
                )}
              </div>
            </div>
            {verifyMethod === "api_token" && (
              <div className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line leading-relaxed">
                {`🔑 Вам будет выдан API ключ, который нужно:
  1. Скопировать
  2. Добавить в .env файл вашего сайта как SAFESCAN_API_KEY
  3. Перезапустить сайт

✅ SafeScan автоматически проверит наличие ключа.
💡 Ключ также будет доступен во вкладке «API ключи».`}
              </div>
            )}
            {verifyMethod === "dns" && (
              <div className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line leading-relaxed">
                {newDomain
                  ? `📝 Вам нужно будет добавить TXT-запись в DNS:
  • Имя: _safescan-verify.${newDomain}
  • Тип: TXT
  • Значение: будет предоставлено после добавления

⏱️ DNS может обновляться от 1 до 60 минут.
✅ SafeScan автоматически проверит запись каждые 5 секунд.`
                  : `📝 Вам нужно будет добавить TXT-запись в DNS вашего домена.
  Имя записи: _safescan-verify
  Тип: TXT

⏱️ DNS может обновляться от 1 до 60 минут.
✅ SafeScan автоматически проверит запись каждые 5 секунд.`}
              </div>
            )}
            {verifyMethod === "file" && (
              <div className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line leading-relaxed">
                {newDomain
                  ? `📁 Вам нужно будет создать файл на сайте:
  • URL: https://${newDomain}/.well-known/safescan-verify.txt
  • Содержимое: будет предоставлено после добавления

✅ SafeScan автоматически проверит файл каждые 5 секунд.`
                  : `📁 Вам нужно будет создать файл на вашем сайте:
  • Путь: /.well-known/safescan-verify.txt
  • Содержимое: будет предоставлено после добавления

✅ SafeScan автоматически проверит файл каждые 5 секунд.`}
              </div>
            )}
          </div>

          <div className="flex gap-3 justify-end">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setShowAddModal(false);
                setError("");
                setNewDomain("");
              }}
            >
              Отмена
            </Button>
            <Button type="submit" disabled={!newDomain.trim()}>
              Добавить
            </Button>
          </div>
        </form>
      </Modal>

      {/* Result Modal — shows API key + instructions for api_token, or verification instructions for others */}
      <Modal
        isOpen={!!addedResult}
        onClose={() => {
          setAddedResult(null);
          setAutoCheckCount(0);
        }}
        title={
          addedResult?.is_verified
            ? "Домен верифицирован!"
            : "Верификация домена"
        }
        size="lg"
      >
        {addedResult && (
          <div className="space-y-5">
            {/* API Token result — key + instructions */}
            {addedResult.api_key && (
              <>
                {addedResult._regenerated && (
                  <div className="flex items-center gap-3 p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
                    <AlertCircle className="w-5 h-5 text-orange-600 dark:text-orange-400 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-semibold text-orange-800 dark:text-orange-300">
                        API ключ перегенерирован
                      </p>
                      <p className="text-xs text-orange-600 dark:text-orange-400 mt-0.5">
                        Предыдущий ключ больше не действителен. Обновите его в
                        .env вашего сайта.
                      </p>
                    </div>
                  </div>
                )}
                {!addedResult._regenerated && !addedResult._just_verified && (
                  <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center flex-shrink-0">
                      <KeyRound className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-blue-800 dark:text-blue-300">
                        Домен «{addedResult.domain}» добавлен
                      </p>
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                        Скопируйте API ключ и добавьте его в .env вашего сайта
                      </p>
                    </div>
                  </div>
                )}
                {addedResult._just_verified && (
                  <div className="flex items-center gap-3 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
                    <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                        Домен «{addedResult.domain}» верифицирован!
                      </p>
                      <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-0.5">
                        API ключ создан. Скопируйте его и добавьте в .env вашего
                        сайта
                      </p>
                    </div>
                  </div>
                )}

                {/* API Key */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Ваш API ключ
                  </h4>
                  <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                    <code className="text-xs flex-1 font-mono text-gray-900 dark:text-white break-all">
                      {addedResult.api_key}
                    </code>
                    <button
                      onClick={() => handleCopy(addedResult.api_key, "apikey")}
                      className={`p-2 rounded-lg transition-colors flex-shrink-0 ${
                        copiedField === "apikey"
                          ? "bg-green-100 dark:bg-green-900/30 text-green-600"
                          : "bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500"
                      }`}
                    >
                      {copiedField === "apikey" ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Env line */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Добавьте в .env файл вашего сайта:
                  </h4>
                  <div className="flex items-center gap-2 p-3 bg-gray-900 dark:bg-gray-800 rounded-lg border border-gray-700">
                    <code className="text-xs flex-1 font-mono text-green-400 break-all">
                      {addedResult.env_line}
                    </code>
                    <button
                      onClick={() =>
                        handleCopy(addedResult.env_line, "envline")
                      }
                      className={`p-2 rounded-lg transition-colors flex-shrink-0 ${
                        copiedField === "envline"
                          ? "bg-green-900/30 text-green-400"
                          : "bg-gray-700 text-gray-400 hover:bg-gray-600"
                      }`}
                    >
                      {copiedField === "envline" ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Instructions */}
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Инструкция
                  </h4>
                  <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line leading-relaxed">
                    {`📋 Что нужно сделать:
  1. Скопируйте API ключ (см. выше)
  2. Откройте файл .env вашего сайта
  3. Добавьте строку: ${addedResult.env_line}
  4. Перезапустите ваш сайт

💡 API ключ также доступен во вкладке «API ключи» —
  вы можете скопировать его в любое время.

⏱️ После добавления ключа SafeScan автоматически проверит
  наличие ключа каждые 5 секунд. Также вы можете
  нажать кнопку «Проверить сейчас».`}
                  </div>
                </div>

                <p className="text-xs text-gray-500 dark:text-gray-400">
                  После верификации ключ навсегда сохранится во вкладке «API
                  ключи».
                </p>

                {/* Auto-check status */}
                <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-blue-800 dark:text-blue-300">
                      Автоматическая проверка…
                    </p>
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                      Проверка #{autoCheckCount} · Проверяем наличие ключа
                    </p>
                  </div>
                </div>
              </>
            )}

            {/* DNS/File verification instructions — ONLY show when NOT api_token */}
            {!addedResult.api_key && addedResult.instructions && (
              <>
                {/* Auto-check status */}
                <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-blue-800 dark:text-blue-300">
                      Автоматическая проверка…
                    </p>
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
                      Проверка #{autoCheckCount} · Проверяем наличие токена
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Инструкция
                  </h4>
                  <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line">
                      {addedResult.instructions}
                    </p>
                  </div>
                </div>

                {addedResult.verification_token &&
                  addedResult.verification_method === "file" && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                        Содержимое файла
                      </h4>
                      <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                        <code className="text-sm flex-1 font-mono text-gray-900 dark:text-white break-all">
                          {addedResult.verification_token}
                        </code>
                        <button
                          onClick={() =>
                            handleCopy(addedResult.verification_token, "token")
                          }
                          className={`p-2 rounded-lg transition-colors flex-shrink-0 ${
                            copiedField === "token"
                              ? "bg-green-100 dark:bg-green-900/30 text-green-600"
                              : "bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500"
                          }`}
                        >
                          {copiedField === "token" ? (
                            <Check className="w-4 h-4" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                {addedResult.dns_record_value &&
                  addedResult.verification_method === "dns" && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                        Значение DNS TXT записи
                      </h4>
                      <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                        <code className="text-sm flex-1 font-mono text-gray-900 dark:text-white break-all">
                          {addedResult.dns_record_value}
                        </code>
                        <button
                          onClick={() =>
                            handleCopy(addedResult.dns_record_value, "dns")
                          }
                          className={`p-2 rounded-lg transition-colors flex-shrink-0 ${
                            copiedField === "dns"
                              ? "bg-green-100 dark:bg-green-900/30 text-green-600"
                              : "bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500"
                          }`}
                        >
                          {copiedField === "dns" ? (
                            <Check className="w-4 h-4" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}
              </>
            )}

            {/* Action buttons */}
            <div className="flex gap-3 justify-end pt-2">
              <Button
                variant="ghost"
                onClick={() => {
                  setAddedResult(null);
                  setAutoCheckCount(0);
                }}
              >
                Закрыть
              </Button>
              <Button
                onClick={async () => {
                  if (addedResult) {
                    const resp = await domainsApi.verify(
                      addedResult.domain_id || addedResult.id,
                    );
                    if (resp.data.is_verified) {
                      setSuccess(
                        `Домен "${addedResult.domain}" верифицирован!`,
                      );
                      setAddedResult(null);
                      setAutoCheckCount(0);
                      await fetchDomains();
                      setTimeout(() => setSuccess(""), 3000);
                    }
                  }
                }}
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Проверить сейчас
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Verification Status Modal (for existing domains) */}
      <Modal
        isOpen={!!verifStatus}
        onClose={() => setVerifStatus(null)}
        title="Верификация домена"
        size="lg"
      >
        {verifStatus && (
          <div className="space-y-4">
            {/* Fallback: show when verification_method is null/empty and no data */}
            {!verifStatus.verification_method &&
              !verifStatus.dns_record_value &&
              !verifStatus.verification_token && (
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                      Метод верификации не установлен
                    </p>
                    <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                      Этот домен был добавлен до обновления системы. Удалите и
                      добавьте домен заново, выбрав метод верификации
                      (рекомендуем API Token для мгновенной верификации).
                    </p>
                  </div>
                </div>
              )}

            {verifStatus.instructions &&
              verifStatus.instructions.trim() !== "" && (
                <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line">
                    {verifStatus.instructions}
                  </p>
                </div>
              )}
            {verifStatus.dns_record_value &&
              verifStatus.verification_method === "dns" && (
                <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <code className="text-sm flex-1 font-mono">
                    {verifStatus.dns_record_value}
                  </code>
                  <button
                    onClick={() =>
                      navigator.clipboard.writeText(
                        verifStatus.dns_record_value!,
                      )
                    }
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              )}
            {verifStatus.verification_token &&
              verifStatus.verification_method === "file" && (
                <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <code className="text-sm flex-1 font-mono">
                    {verifStatus.verification_token}
                  </code>
                  <button
                    onClick={() =>
                      navigator.clipboard.writeText(
                        verifStatus.verification_token!,
                      )
                    }
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              )}
            {verifStatus.verification_method === "api_token" && (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex items-start gap-3">
                <KeyRound className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-800 dark:text-blue-300">
                    API ключ
                  </p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    API ключ для этого домена доступен во вкладке «API ключи».
                    Вы можете скопировать его оттуда в любое время.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
