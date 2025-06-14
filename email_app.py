package com.example.emailportal;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import javax.annotation.PostConstruct;
import java.io.*;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Controller
public class EmailController {

    @Autowired
    private Environment env;

    private List<Map<String, String>> emailAccounts = new ArrayList<>();

    private final String CSV_FILE_PATH = "emails.csv";

    @PostConstruct
    public void init() {
        Map<String, String> account1 = new HashMap<>();
        account1.put("MAIL_USERNAME", env.getProperty("MAIL_USERNAME_1"));
        account1.put("MAIL_PASSWORD", env.getProperty("MAIL_PASSWORD_1"));

        Map<String, String> account2 = new HashMap<>();
        account2.put("MAIL_USERNAME", env.getProperty("MAIL_USERNAME_2"));
        account2.put("MAIL_PASSWORD", env.getProperty("MAIL_PASSWORD_2"));

        emailAccounts.add(account1);
        emailAccounts.add(account2);
    }

    @GetMapping("/")
    public String index(@RequestParam(value = "search", required = false) String search, Model model) {
        List<EmailEntry> emailList = new ArrayList<>();

        try (BufferedReader br = new BufferedReader(new FileReader(CSV_FILE_PATH))) {
            String line;
            while ((line = br.readLine()) != null) {
                String[] values = line.split(",", -1);
                if (values.length >= 4) {
                    EmailEntry entry = new EmailEntry(values[0], values[1], values[2], values[3], LocalDateTime.now().toString());
                    emailList.add(entry);
                }
            }
        } catch (IOException e) {
            // File might not exist
        }

        if (search != null && !search.isEmpty()) {
            emailList = emailList.stream().filter(email ->
                    email.getRecipient().toLowerCase().contains(search.toLowerCase()) ||
                            email.getSubject().toLowerCase().contains(search.toLowerCase())
            ).collect(Collectors.toList());
        }

        model.addAttribute("emails", emailList);
        model.addAttribute("searchQuery", search);
        return "index";
    }

    @PostMapping("/send-email")
    public String sendEmail(@RequestParam("recipient_email") String recipient,
                            @RequestParam("subject") String subject,
                            @RequestParam("message") String message,
                            RedirectAttributes redirectAttributes) {

        for (Map<String, String> account : emailAccounts) {
            try {
                JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
                mailSender.setHost(env.getProperty("MAIL_SERVER"));
                mailSender.setPort(Integer.parseInt(env.getProperty("MAIL_PORT")));
                mailSender.setUsername(account.get("MAIL_USERNAME"));
                mailSender.setPassword(account.get("MAIL_PASSWORD"));
                mailSender.getJavaMailProperties().put("mail.smtp.auth", true);
                mailSender.getJavaMailProperties().put("mail.smtp.starttls.enable", env.getProperty("MAIL_USE_TLS"));

                SimpleMailMessage msg = new SimpleMailMessage();
                msg.setFrom(account.get("MAIL_USERNAME"));
                msg.setTo(recipient);
                msg.setSubject(subject);
                msg.setText(message);

                mailSender.send(msg);

                try (BufferedWriter writer = new BufferedWriter(new FileWriter(CSV_FILE_PATH, true))) {
                    writer.write(String.format("%s,%s,%s,%s\n", account.get("MAIL_USERNAME"), recipient, subject, message));
                }

                redirectAttributes.addFlashAttribute("message", "Email sent successfully from " + account.get("MAIL_USERNAME") + "!");
                redirectAttributes.addFlashAttribute("alertClass", "success");

            } catch (Exception e) {
                redirectAttributes.addFlashAttribute("message", "Error sending email from " + account.get("MAIL_USERNAME") + ": " + e.getMessage());
                redirectAttributes.addFlashAttribute("alertClass", "danger");
            }
        }
        return "redirect:/";
    }
}
