// AI Chat — shinyjson example
// Converts the upstream shiny-react 7-chat example to the shinyjson pattern.
// All React UI is built with React.createElement (aliased as `h`).
(function () {
  var React = window.shinyjson.React;
  var h = React.createElement;
  var useShinyInput = window.shinyjson.useShinyInput;
  var useShinyMessageHandler = window.shinyjson.useShinyMessageHandler;

  var useState = React.useState;
  var useEffect = React.useEffect;
  var useRef = React.useRef;
  var useCallback = React.useCallback;

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------
  var MAX_FILE_SIZE_MB = 5;
  var SUPPORTED_IMAGE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
  ];

  // ---------------------------------------------------------------------------
  // Theme definitions
  // ---------------------------------------------------------------------------
  var themes = [
    { name: "default", displayName: "Default", description: "Clean and minimal" },
    { name: "paper", displayName: "Paper", description: "Notebook and ink" },
    { name: "cyberpunk", displayName: "Cyberpunk", description: "Neon and electric" },
    { name: "glassmorphism", displayName: "Glass", description: "Frosted glass effects" },
    { name: "terminal", displayName: "Terminal", description: "Retro computing" },
    { name: "discord", displayName: "Discord", description: "Familiar chat style" },
  ];

  // ---------------------------------------------------------------------------
  // Theme context via simple React context
  // ---------------------------------------------------------------------------
  var ThemeContext = React.createContext(undefined);

  function useTheme() {
    var ctx = React.useContext(ThemeContext);
    if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
    return ctx;
  }

  function ThemeProvider(props) {
    var _s = useState("default");
    var currentTheme = _s[0];
    var setCurrentTheme = _s[1];

    // Load saved theme
    useEffect(function () {
      var saved = localStorage.getItem("chat-theme");
      if (saved && themes.find(function (t) { return t.name === saved; })) {
        setCurrentTheme(saved);
      }
    }, []);

    // Apply theme class to document root
    useEffect(function () {
      var root = document.documentElement;
      themes.forEach(function (t) {
        root.classList.remove("theme-" + t.name);
      });
      root.classList.add("theme-" + currentTheme);
    }, [currentTheme]);

    function setTheme(name) {
      setCurrentTheme(name);
      localStorage.setItem("chat-theme", name);
    }

    function getTheme(name) {
      return themes.find(function (t) { return t.name === name; }) || themes[0];
    }

    return h(
      ThemeContext.Provider,
      { value: { currentTheme: currentTheme, setTheme: setTheme, getTheme: getTheme } },
      props.children
    );
  }

  // ---------------------------------------------------------------------------
  // SVG icon helpers (replacing lucide-react)
  // ---------------------------------------------------------------------------
  function BotIcon(props) {
    var size = (props && props.size) || 24;
    return h(
      "svg",
      { xmlns: "http://www.w3.org/2000/svg", width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", className: props && props.className },
      h("path", { d: "M12 8V4H8" }),
      h("rect", { width: "16", height: "12", x: "4", y: "8", rx: "2" }),
      h("path", { d: "M2 14h2" }),
      h("path", { d: "M20 14h2" }),
      h("path", { d: "M15 13v2" }),
      h("path", { d: "M9 13v2" })
    );
  }

  function UserIcon(props) {
    var size = (props && props.size) || 24;
    return h(
      "svg",
      { xmlns: "http://www.w3.org/2000/svg", width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", className: props && props.className },
      h("path", { d: "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" }),
      h("circle", { cx: "12", cy: "7", r: "4" })
    );
  }

  function SendIcon(props) {
    var size = (props && props.size) || 24;
    return h(
      "svg",
      { xmlns: "http://www.w3.org/2000/svg", width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", className: props && props.className },
      h("path", { d: "m22 2-7 20-4-9-9-4Z" }),
      h("path", { d: "M22 2 11 13" })
    );
  }

  function PlusIcon(props) {
    var size = (props && props.size) || 24;
    return h(
      "svg",
      { xmlns: "http://www.w3.org/2000/svg", width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", className: props && props.className },
      h("path", { d: "M5 12h14" }),
      h("path", { d: "M12 5v14" })
    );
  }

  function XIcon(props) {
    var size = (props && props.size) || 24;
    return h(
      "svg",
      { xmlns: "http://www.w3.org/2000/svg", width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", className: props && props.className },
      h("path", { d: "M18 6 6 18" }),
      h("path", { d: "m6 6 12 12" })
    );
  }

  function PaletteIcon(props) {
    var size = (props && props.size) || 24;
    return h(
      "svg",
      { xmlns: "http://www.w3.org/2000/svg", width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", className: props && props.className },
      h("circle", { cx: "13.5", cy: "6.5", r: ".5", fill: "currentColor" }),
      h("circle", { cx: "17.5", cy: "10.5", r: ".5", fill: "currentColor" }),
      h("circle", { cx: "8.5", cy: "7.5", r: ".5", fill: "currentColor" }),
      h("circle", { cx: "6.5", cy: "12.5", r: ".5", fill: "currentColor" }),
      h("path", { d: "M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z" })
    );
  }

  function ChevronDownIcon(props) {
    var size = (props && props.size) || 24;
    return h(
      "svg",
      { xmlns: "http://www.w3.org/2000/svg", width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", className: props && props.className, style: props && props.style },
      h("path", { d: "m6 9 6 6 6-6" })
    );
  }

  // ---------------------------------------------------------------------------
  // Image upload helpers (plain functions)
  // ---------------------------------------------------------------------------
  function validateFile(file) {
    if (SUPPORTED_IMAGE_TYPES.indexOf(file.type) === -1) {
      return "File type " + file.type + " is not supported. Please use JPEG, PNG, WebP, or GIF.";
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      return "File size must be less than " + MAX_FILE_SIZE_MB + "MB.";
    }
    return null;
  }

  function processFiles(files) {
    var fileArray = Array.from(files);
    var promises = fileArray.map(function (file) {
      var error = validateFile(file);
      if (error) {
        alert(error);
        return Promise.resolve(null);
      }
      return new Promise(function (resolve) {
        var reader = new FileReader();
        reader.onload = function () {
          var result = reader.result;
          var base64 = result.split(",")[1];
          resolve({
            name: file.name,
            content: base64,
            type: file.type,
            size: file.size,
          });
        };
        reader.readAsDataURL(file);
      });
    });
    return Promise.all(promises).then(function (results) {
      return results.filter(function (r) { return r !== null; });
    });
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  // ---------------------------------------------------------------------------
  // Simple markdown-to-HTML (basic formatting, no external lib)
  // ---------------------------------------------------------------------------
  // TODO: XSS risk — only code blocks are escaped via escapeHtml(). Text
  // outside code blocks (inline code, bold, italic, plain text) is inserted
  // as raw HTML via dangerouslySetInnerHTML. If the AI model returns markup
  // like <img src=x onerror=...>, it will execute. A proper fix needs to
  // escape text while preserving rendered markdown formatting (e.g., use a
  // sanitization library like DOMPurify, or build a React element tree
  // instead of an HTML string).
  function renderMarkdown(text) {
    if (!text) return "";
    var html = text
      // Code blocks (triple backtick)
      .replace(/```(\w*)\n([\s\S]*?)```/g, function (_m, _lang, code) {
        return '<pre class="md-code-block"><code>' + escapeHtml(code.trim()) + "</code></pre>";
      })
      // Inline code
      .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
      // Bold
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      // Italic
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      // Line breaks
      .replace(/\n/g, "<br>");
    return html;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ---------------------------------------------------------------------------
  // ThemeSwitcher component
  // ---------------------------------------------------------------------------
  function ThemeSwitcher() {
    var theme = useTheme();
    var currentTheme = theme.currentTheme;
    var setTheme = theme.setTheme;
    var getTheme = theme.getTheme;

    var _open = useState(false);
    var isOpen = _open[0];
    var setIsOpen = _open[1];
    var dropdownRef = useRef(null);

    useEffect(function () {
      function handleClickOutside(event) {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
          setIsOpen(false);
        }
      }
      document.addEventListener("mousedown", handleClickOutside);
      return function () {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }, []);

    var currentThemeData = getTheme(currentTheme);

    var themePreviewColors = {
      default: "#f3f4f6",
      paper: "#ffffff",
      cyberpunk: "linear-gradient(45deg, #22d3ee, #ec4899)",
      glassmorphism: "linear-gradient(45deg, rgba(59,130,246,0.3), rgba(168,85,247,0.3))",
      terminal: "#000000",
      discord: "#2f3349",
    };

    return h(
      "div",
      { className: "theme-switcher", ref: dropdownRef },
      h(
        "button",
        {
          className: "theme-switcher-btn",
          onClick: function () { setIsOpen(!isOpen); },
          title: "Change theme",
        },
        h(PaletteIcon, { size: 16 }),
        h("span", { className: "theme-switcher-label" }, currentThemeData.displayName),
        h(ChevronDownIcon, {
          size: 16,
          style: { transform: isOpen ? "rotate(180deg)" : "none", transition: "transform 0.2s" },
        })
      ),
      isOpen
        ? h(
            "div",
            { className: "theme-dropdown" },
            h("div", { className: "theme-dropdown-title" }, "Choose Theme"),
            themes.map(function (t) {
              return h(
                "button",
                {
                  key: t.name,
                  className: "theme-option" + (currentTheme === t.name ? " active" : ""),
                  onClick: function () {
                    setTheme(t.name);
                    setIsOpen(false);
                  },
                },
                h("span", {
                  className: "theme-color-dot",
                  style: {
                    background: themePreviewColors[t.name] || "#ccc",
                    border: t.name === "paper" ? "2px solid #1e40af" : "2px solid transparent",
                  },
                }),
                h(
                  "span",
                  { className: "theme-option-text" },
                  h("span", { className: "theme-option-name" }, t.displayName),
                  h("span", { className: "theme-option-desc" }, t.description)
                ),
                currentTheme === t.name
                  ? h("span", { className: "theme-active-dot" })
                  : null
              );
            })
          )
        : null
    );
  }

  // ---------------------------------------------------------------------------
  // ImagePreview component
  // ---------------------------------------------------------------------------
  function ImagePreview(props) {
    var attachments = props.attachments;
    var onRemove = props.onRemove;
    var isLoading = props.isLoading;

    if (!attachments || attachments.length === 0) return null;

    return h(
      "div",
      { className: "image-preview-area" },
      h(
        "div",
        { className: "image-preview-label" },
        attachments.length + " image" + (attachments.length !== 1 ? "s" : "") + " attached"
      ),
      h(
        "div",
        { className: "image-preview-grid" },
        attachments.map(function (att, index) {
          return h(
            "div",
            { key: index, className: "image-preview-item" },
            h("img", {
              src: "data:" + att.type + ";base64," + att.content,
              alt: att.name,
              className: "image-preview-img",
            }),
            h(
              "button",
              {
                className: "image-remove-btn",
                onClick: function () { onRemove(index); },
                disabled: isLoading,
                "aria-label": "Remove " + att.name,
              },
              h(XIcon, { size: 12 })
            ),
            h(
              "div",
              { className: "image-preview-info" },
              h("span", { className: "image-preview-name", title: att.name }, att.name),
              h("span", { className: "image-preview-size" }, formatFileSize(att.size))
            )
          );
        })
      )
    );
  }

  // ---------------------------------------------------------------------------
  // ChatInterface component
  // ---------------------------------------------------------------------------
  function ChatInterface(props) {
    var theme = useTheme();
    var currentTheme = theme.currentTheme;

    // Shiny input for sending chat messages
    var _input = useShinyInput(props.input_id, { text: "", attachments: [] }, { debounceMs: 0, priority: "event" });
    var setCurrentMessage = _input[1];

    var _msgs = useState([]);
    var messages = _msgs[0];
    var setMessages = _msgs[1];

    var _loading = useState(false);
    var isLoading = _loading[0];
    var setIsLoading = _loading[1];

    var _inputVal = useState("");
    var inputValue = _inputVal[0];
    var setInputValue = _inputVal[1];

    var _attachments = useState([]);
    var currentAttachments = _attachments[0];
    var setCurrentAttachments = _attachments[1];

    var _dragOver = useState(false);
    var isDragOver = _dragOver[0];
    var setIsDragOver = _dragOver[1];
    var dragCounterRef = useRef(0);

    var scrollAreaRef = useRef(null);
    var messagesEndRef = useRef(null);
    var fileInputRef = useRef(null);

    // Handle streaming messages from Shiny server
    useShinyMessageHandler("chat_stream", function (msg) {
      if (msg.done) {
        setIsLoading(false);
      } else {
        setMessages(function (prev) {
          var newMessages = prev.slice();
          var last = newMessages[newMessages.length - 1];
          if (last && last.role === "assistant") {
            // Clone and append chunk
            newMessages[newMessages.length - 1] = Object.assign({}, last, {
              content: last.content + msg.chunk,
            });
          } else {
            newMessages.push({
              id: Date.now().toString(),
              role: "assistant",
              content: msg.chunk,
              timestamp: new Date(),
            });
          }
          return newMessages;
        });
      }
    });

    // Auto-scroll to bottom
    useEffect(function () {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, [messages]);

    var handleSendMessage = useCallback(function () {
      if ((!inputValue.trim() && currentAttachments.length === 0) || isLoading) return;

      var userMessage = {
        id: Date.now().toString(),
        role: "user",
        content: inputValue.trim(),
        attachments: currentAttachments.length > 0 ? currentAttachments.slice() : undefined,
        timestamp: new Date(),
      };

      var assistantPlaceholder = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };

      setMessages(function (prev) { return prev.concat([userMessage, assistantPlaceholder]); });
      setIsLoading(true);

      setCurrentMessage({
        text: inputValue.trim(),
        attachments: currentAttachments.slice(),
      });

      setInputValue("");
      setCurrentAttachments([]);
    }, [inputValue, currentAttachments, isLoading, setCurrentMessage]);

    function handleKeyPress(e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    }

    function formatTime(date) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    // File handling
    function handleFilesSelected(files) {
      if (isLoading) return;
      processFiles(files).then(function (newAttachments) {
        if (newAttachments.length > 0) {
          setCurrentAttachments(function (prev) { return prev.concat(newAttachments); });
        }
      });
    }

    function handleFileInputChange(e) {
      var files = e.target.files;
      if (files && files.length > 0) {
        handleFilesSelected(files);
      }
      e.target.value = "";
    }

    function handleDragEnter(e) {
      e.preventDefault();
      e.stopPropagation();
      dragCounterRef.current++;
      if (e.dataTransfer.types.indexOf("Files") !== -1) {
        setIsDragOver(true);
      }
    }

    function handleDragLeave(e) {
      e.preventDefault();
      e.stopPropagation();
      dragCounterRef.current--;
      if (dragCounterRef.current <= 0) {
        setIsDragOver(false);
        dragCounterRef.current = 0;
      }
    }

    function handleDragOver(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    function handleDrop(e) {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      dragCounterRef.current = 0;
      var files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFilesSelected(files);
      }
    }

    function removeAttachment(index) {
      setCurrentAttachments(function (prev) {
        return prev.filter(function (_, i) { return i !== index; });
      });
    }

    var canSend = (inputValue.trim() || currentAttachments.length > 0) && !isLoading;

    // -------------------------------------------------------------------------
    // Render
    // -------------------------------------------------------------------------
    return h(
      "div",
      { className: "chat-container" },
      h(
        "div",
        { className: "chat-card", "data-card": true },
        // Header
        h(
          "div",
          { className: "chat-header" },
          h(
            "div",
            { className: "chat-header-left" },
            h(BotIcon, { size: 24 }),
            h("span", { className: "chat-title" }, "AI Chat"),
            h("span", { className: "chat-theme-badge theme-badge-" + currentTheme }, currentTheme)
          ),
          h(ThemeSwitcher, null)
        ),

        // Messages area
        h(
          "div",
          { className: "chat-messages", ref: scrollAreaRef },
          h(
            "div",
            { className: "chat-messages-inner" },
            messages.length === 0
              ? h(
                  "div",
                  { className: "chat-empty" },
                  h(BotIcon, { size: 32 }),
                  h("p", null, "Start a conversation with the AI assistant")
                )
              : null,
            messages.map(function (message) {
              var isUser = message.role === "user";
              return h(
                "div",
                {
                  key: message.id,
                  className: "message-row" + (isUser ? " message-row-user" : " message-row-assistant"),
                },
                // Avatar
                h(
                  "div",
                  { className: "avatar" + (isUser ? " avatar-user" : " avatar-assistant") },
                  isUser
                    ? h(UserIcon, { size: 16 })
                    : h(BotIcon, { size: 16 })
                ),
                // Bubble
                h(
                  "div",
                  { className: "message-bubble" + (isUser ? " message-user" : " message-assistant") },
                  message.content === "" && message.role === "assistant" && isLoading
                    ? h(
                        "div",
                        { className: "typing-dots" },
                        h("div", { className: "typing-indicator" }),
                        h("div", { className: "typing-indicator" }),
                        h("div", { className: "typing-indicator" })
                      )
                    : h(
                        "div",
                        null,
                        message.content
                          ? h("div", {
                              className: "message-text",
                              dangerouslySetInnerHTML: { __html: renderMarkdown(message.content) },
                            })
                          : null,
                        // Attachments in message
                        message.attachments && message.attachments.length > 0
                          ? h(
                              "div",
                              { className: "message-attachments" },
                              message.attachments.map(function (att, idx) {
                                return h(
                                  "div",
                                  { key: idx, className: "message-attachment-item" },
                                  h("img", {
                                    src: "data:" + att.type + ";base64," + att.content,
                                    alt: att.name,
                                    className: "message-attachment-img",
                                  }),
                                  h(
                                    "div",
                                    { className: "message-attachment-name" },
                                    att.name
                                  )
                                );
                              })
                            )
                          : null,
                        h(
                          "div",
                          { className: "message-time" + (isUser ? " message-time-right" : "") },
                          formatTime(message.timestamp)
                        )
                      )
                )
              );
            }),
            h("div", { ref: messagesEndRef })
          )
        ),

        // Input area
        h(
          "div",
          { className: "chat-input-area" },
          h(
            "div",
            { className: "chat-input-inner" },
            // Image preview
            h(ImagePreview, {
              attachments: currentAttachments,
              onRemove: removeAttachment,
              isLoading: isLoading,
            }),
            // Input row with drag-and-drop
            h(
              "div",
              {
                className: "chat-input-row" + (isDragOver && !isLoading ? " drag-over" : "") + (isLoading ? " input-disabled" : ""),
                onDrop: handleDrop,
                onDragEnter: handleDragEnter,
                onDragLeave: handleDragLeave,
                onDragOver: handleDragOver,
              },
              // Hidden file input
              h("input", {
                ref: fileInputRef,
                type: "file",
                className: "sr-only",
                accept: SUPPORTED_IMAGE_TYPES.join(","),
                multiple: true,
                onChange: handleFileInputChange,
                disabled: isLoading,
              }),
              // Plus button
              h(
                "button",
                {
                  className: "icon-btn",
                  onClick: function () { if (fileInputRef.current) fileInputRef.current.click(); },
                  disabled: isLoading,
                  "aria-label": "Attach images",
                  title: "Attach images",
                },
                h(PlusIcon, { size: 16 })
              ),
              // Text input
              h("input", {
                type: "text",
                className: "chat-text-input",
                value: inputValue,
                onChange: function (e) { setInputValue(e.target.value); },
                onKeyDown: handleKeyPress,
                placeholder: isDragOver ? "Drop images here..." : "Type your message here...",
                disabled: isLoading,
              }),
              // Send button
              h(
                "button",
                {
                  className: "send-btn",
                  onClick: handleSendMessage,
                  disabled: !canSend,
                  "aria-label": "Send message",
                  title: "Send message",
                },
                h(SendIcon, { size: 16 })
              ),
              // Drag overlay
              isDragOver && !isLoading
                ? h("div", { className: "drag-overlay" }, "Drop images here")
                : null
            )
          )
        )
      )
    );
  }

  // ---------------------------------------------------------------------------
  // App wrapper (provides theme context)
  // ---------------------------------------------------------------------------
  function ChatApp(args) {
    var props = args.element.props;
    return h(ThemeProvider, null, h(ChatInterface, { input_id: props.input_id }));
  }

  // ---------------------------------------------------------------------------
  // Register with shinyjson
  // ---------------------------------------------------------------------------
  window.shinyjson.registerComponents(null, {
    ChatApp: ChatApp,
  });
})();
